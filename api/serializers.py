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
    
    # @classmethod
    # def get_token(cls, user):
    #     token = super().get_token(user)

    #     # Set the life time of the token to 12 hours.
    #     token['exp'] = datetime.utcnow() + timedelta(hours=os.environ('TOKEN_EXP_TIME'))

    #     return token

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
    answer_options = AnswerOptionSerializer(source='answeroption_set', many=True, read_only=True)

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
        if question:
            if question.type == 'text':
                raise serializers.ValidationError({'question': "Question object must NOT be of type 'text'."})
            return super().create(validated_data)
        raise exceptions.NotFound(detail='A Question with the given ID could not be found.')


# Question serializer
class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(source='option_set', many=True, read_only=True)

    class Meta:
        model = Question
        exclude = ['form']

    def update(self, instance, validated_data):
        # Check if type is text and delete all options
        if validated_data.get('type') == 'text':
            instance.options.all().delete()
        # Call the superclass update method to update the Question object
        question = super().update(instance, validated_data)
        return question

# Response serializer
class ResponseSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    date_created = serializers.DateTimeField(read_only=True)
    questions = QuestionSerializer(source='question_set', many=True, read_only=True)

    class Meta:
        model = Response
        fields = '__all__'

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