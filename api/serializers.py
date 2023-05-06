# from datetime import datetime, timedelta
from rest_framework import serializers, exceptions
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# import os

from .models import Form, Question, Option, Response, Answer, AnswerOption

# Serializer for User elements.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value: str) -> str:
        """
        Hash value passed by user.

        :param value: password of a user
        :return: a hashed version of the password
        """
        return make_password(value)
    

# Serializer to retrieve only the Access Token
# from the simple-jwt token generation system.
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data['access'] = str(refresh.access_token)
        del data['refresh']
        
        return data


# AnswerOption serializer
class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = '__all__'


# Answer serializer
class AnswerSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(source='answeroption_set', many=True)

    class Meta:
        model = Answer
        fields = '__all__'


# Option serializer
class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        exclude = ['question']

    # Override the default create() method to raise a ValidationError exception
    # if the user is trying to link the Option to a Question of type 'text'.
    def create(self, validated_data):
        question = validated_data.get('question')
        if question.type == 'text':
            raise serializers.ValidationError({'question': "Question object must NOT be of type 'text'."})
        
        # Update the 'date_updated' field from the Form.
        form = question.form
        form.update_date_updated()

        # Create the new Option.
        return super().create(validated_data)
    
    # Override the default update() method to raise a ValidationError exception
    # if the user is trying to link the Option to a Question of type 'text'.
    def update(self, instance, validated_data):
        # Update the 'date_updated' field from the Form.
        form = instance.question.form
        form.update_date_updated()

        # Update the Option.
        return super().update(instance, validated_data)


# Question serializer
class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(source='option_set', many=True, read_only=True)

    class Meta:
        model = Question
        exclude = ['form']

    def update(self, instance, validated_data):
        # TODO: Check if type is text and delete all options.
        if validated_data.get('type') == 'text':
            Option.objects.filter(question=instance).delete()

        # Call the superclass update method to update the Question object.
        question = super().update(instance, validated_data)

        # Update the Form's date_updated field.
        form = Form.objects.get(pk=instance.form.pk)
        form.update_date_updated()
        
        return question

    def create(self, validated_data):
        # Get the Form that the Question should be linked to.
        form = Form.objects.get(pk=validated_data.get('form').pk)

        # Update the From's date_updated field.
        form.update_date_updated()

        # Create the new Question object.
        return super().create(validated_data)


# Response serializer
class ResponseSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    date_created = serializers.DateTimeField(read_only=True)
    answers = AnswerSerializer(source='answer_set', many=True, read_only=True)

    class Meta:
        model = Response
        fields = '__all__'

    # Add the Form's id and 'answers' to the data sent by the user before it gets validated.
    def to_internal_value(self, data):
        # Get the Form ID from the request and add it to the data to be
        # validated.
        form_id = self.context['request'].parser_context.get('kwargs').get(
        'form_id')
        data['form'] = form_id

        # Get the 'answers' data from the data sent by the user and add it
        # to the data that's already processed and ready to be passed to the
        # validation process.
        answers_data = data.get('answers', None)
        internal_value = super().to_internal_value(data)
        internal_value.update({'answers': answers_data})

        return internal_value
    
    # Override the create() method to create the Answers and AnswerOptions
    # needed and link them to the new Response element.
    def create(self, validated_data):

        print("[validated_data]:")
        print(validated_data)

        # Get the user who made the request.
        user = self.context.get('request').user

        # Get the data from the Answers and remove it from the
        # validated_data
        answers_data = validated_data.pop('answers', None)

        if answers_data == None:
            raise exceptions.ValidationError({'answers': 'This field is required.'})

        # Create the new Response element with the validated data.
        response = Response.objects.create(created_by=user, **validated_data)

        # Create the Answer objects for the Reponse that was just created but first validating
        # the AnswerOptions data.
        for answer_data in answers_data:
            # Get the date from the AnswerOptions from the current Answer data.
            answer_options_data = answer_data.pop('answer_options', [])

            # Get the Question the Answer is answering and make sure it belongs
            # to the same Form that the Response is linked to.
            try:
                question = Question.objects.get(pk=answer_data.get('question'), form=response.form)
            except Question.DoesNotExist:
                raise exceptions.NotFound(detail="A Question with the given 'question' id could not be found.")
            
            # If the Question's type is 'text', then there must be only one
            # AnswerOption.
            if question.type == 'text':
                if len(answer_options_data) != 1:
                    raise exceptions.ValidationError({
                        'answer_options': "Must contain only one AnswerOption for a Question of type 'text'."
                    })

            # If the Question's type is 'multiple', then there must be at least one
            # AnswerOption, and each of them must match the value of an Option from
            # the Question.
            elif question.type == 'multiple':
                if len(answer_options_data) == 0:
                    raise exceptions.ValidationError({
                        'answer_options': "Must contain at least one AnswerOption for a Question of type 'multiple.'"
                    })
                
                # Get the list of Options from the Question and compare their 'value'
                # with the 'value' from the AnswerOptions. 
                question_options = Option.objects.filter(question=question)
                
                # Get a set of unique values from question_options queryset.
                option_values = set(question_options.values_list('value', flat=True))

                # Create a set of unique values from answer_options_data List of dicts.
                answer_values = {option['value'] for option in answer_options_data}

                # Check if each answer_option value is in the question_option values set and is unique.
                if not (answer_values.issubset(option_values) and len(answer_values) == len(answer_options_data)):
                    # At least one answer_option value is invalid or not unique.
                    raise exceptions.ValidationError({
                        'answer_options': "At least one AnswerOption 'value' is invalid or not unique."
                    })
            
            # If the Question's type is 'select', then there must be only one
            # AnswerOption.
            elif question.type == 'select':
                if not len(answer_options_data) == 1:
                    raise exceptions.ValidationError({
                        'answer_options': "Must contain only one AnswerOption for a Question of type 'select'."
                    })
                
                # Get the list of Options from the Question and compare their 'value'
                # with the 'value' from the AnswerOption. 
                question_options = Option.objects.filter(question=question)
                
                # Get a tuple of the values from question_options queryset.
                option_values = question_options.values_list('value', flat=True)

                # If the AnswerOption's value does not correspond to one of the
                # Question Options', raise an error.
                if not answer_options_data[0].get('value') in option_values:
                    raise exceptions.ValidationError({
                        'answer_options': "The 'value' of the AnswerOption does not correspond to a valid option."
                    })

            # Create the new Answer object with its AnswerOptions.
            new_answer = Answer.objects.create(response=response, question=question)
            
            for answer_option_data in answer_options_data:
                AnswerOption.objects.create(answer=new_answer, **answer_option_data)

        return response


# Forms serializer
class FormSerializer(serializers.ModelSerializer):

    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    date_created = serializers.DateTimeField(read_only=True)
    date_updated = serializers.DateTimeField(read_only=True)
    questions = QuestionSerializer(source='question_set', many=True, read_only=True)
    responses = ResponseSerializer(source='response_set', many=True, read_only=True)

    class Meta:
        model = Form
        fields = ['id', 'title', 'description', 'created_by', 'date_created', 'date_updated', 'questions', 'responses']