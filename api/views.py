from django.db.utils import IntegrityError
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Form, Question, Option
from .serializers import UserSerializer, MyTokenObtainPairSerializer, FormSerializer, QuestionSerializer, OptionSerializer


class UserViewSet(viewsets.ViewSet):
    
    """
    ViewSet used to create new User instances through the API.
    """

    serializer_class = UserSerializer

    # Method to create new user with Django's User model.
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class MyTokenObtainPairView(TokenObtainPairView):

    """
    Custom view to use the custom serializer to only return 
    an Access Token in the response, using Simple-JWT's TokenObtainPairView.
    """

    serializer_class = MyTokenObtainPairSerializer


class FormList(generics.ListCreateAPIView):

    """
    View to create a new Form, and get the list of the 
    user's existing Forms.
    """

    serializer_class = FormSerializer
    permission_classes = [IsAuthenticated]

    # The queryset consists of the Forms created by the user
    # that is sending the request.
    def get_queryset(self):
        return Form.objects.all().filter(created_by=self.request.user)

    # We create the new Form instance with the user sending 
    # the request as the "created_by" user.
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FormDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    View to get a specific Form that the user owns with its given id.
    """

    serializer_class = FormSerializer
    permission_classes = [IsAuthenticated]

    # Return the QuerySet with the Form object with the given id
    # through the URL parameters.
    def get_queryset(self):
        form_id = self.kwargs.get('pk')
        if form_id:
            queryset = Form.objects.all().filter(pk=form_id, created_by=self.request.user)
            if not queryset:
                raise NotFound(detail="A Form with the given id was not found")
            return queryset
        
        # Raise a ValidationError if a valid pk was not
        # provided.
        raise ValidationError(detail="A Form with the given id was not found")


class QuestionList(generics.ListCreateAPIView):

    """
    View to create a new Question that should be linked to a given Form,
    or to retrieve a list of a Form's Questions.
    """

    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    # Return a diferent QuerySet depending on the method 
    # used in the request.
    def get_queryset(self):
        form_id = self.kwargs.get('form_id')
        if not form_id:
            raise ValidationError({'form_id': 'Missing URL parameter.'})
        if not Form.objects.all().filter(pk=form_id, created_by=self.request.user):
            raise NotFound(detail="A Form with the given id was not found.")
        
        question_queryset = Question.objects.all().filter(form__pk=form_id)

        return question_queryset


    # First check if the Form with the given form_id exists, 
    # and if the user owns the Form before adding the new Question.
    def perform_create(self, serializer):
        form_id = self.kwargs.get('form_id')
        try:
            form = Form.objects.get(pk=form_id)
            if form.created_by == self.request.user:
                serializer.save(form=form)
            else:
                raise Form.DoesNotExist
        except Form.DoesNotExist:
            raise NotFound(detail="A Form with the given id was not found.")


class QuestionDetail(generics.RetrieveUpdateDestroyAPIView):
    
    """
    View to get, modify or delete an existing Question
    from a given Form.
    """

    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg =  'question_id'

    # Return a diferent QuerySet depending on the method 
    # used in the request.
    def get_queryset(self):
        form_id = self.kwargs.get('form_id')
        question_id = self.kwargs.get('question_id')
        
        # Confirm if form_id and question_id were provided.
        if not form_id:
            raise ValidationError({'form_id': 'Missing URL parameter.'})
        if not question_id:
            raise ValidationError({'question_id': 'Missing URL parameter.'})
        
        # Check if the Form with the given form_id exists.
        try:
            form = Form.objects.get(pk=form_id, created_by=self.request.user)
        except Form.DoesNotExist:
            raise NotFound(detail="A Form with the given form_id could not be found.")
        
        # Check if the Question with the given Form and question_id exists.
        question_queryset = Question.objects.all().filter(form=form, pk=question_id)
        if not question_queryset:
            raise NotFound(detail="A Question with the given question_id could not be found.")

        # Return the queryset with the Question found.
        return question_queryset
    
    # Override perform_destroy to update the 'date_updated' field from
    # the Question's Form before deleting the Question.
    def perform_destroy(self, instance):
        form = instance.form
        form.update_date_updated()
        return super().perform_destroy(instance)


class OptionList(generics.ListCreateAPIView):
    """
    View to create a new Option or get a list of
    them for a given Question.
    """

    serializer_class = OptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.method == 'GET':
            form_id = self.kwargs.get('form_id')
            question_id = self.kwargs.get('question_id')
            
            # Confirm if form_id and question_id were provided.
            if not form_id:
                raise ValidationError({'form_id': 'Missing URL parameter.'})
            if not question_id:
                raise ValidationError({'question_id': 'Missing URL parameter.'})
            
            # Check if the Form with the given form_id exists.
            try:
                form = Form.objects.get(pk=form_id, created_by=self.request.user)
            except Form.DoesNotExist:
                raise NotFound(detail="A Form with the given form_id could not be found.")
            
            # Check if the Question with the given Form and question_id exists.
            question = Question.objects.get(form=form, pk=question_id)
            if not question:
                raise NotFound(detail="A Question with the given question_id could not be found.")
            
            return Option.objects.all().filter(question=question)
        
        return Option.objects.all() 
    
    # First check if the Form and Question with the given ids exist, 
    # and if the user owns the Form before adding the new Option.
    def perform_create(self, serializer):
        form_id = self.kwargs.get('form_id')
        question_id = self.kwargs.get('question_id')
        try:
            form = Form.objects.get(pk=form_id, created_by=self.request.user)
            question = Question.objects.get(pk=question_id, form=form)
            serializer.save(question=question)
        except Form.DoesNotExist:
            raise NotFound(detail="A Form with the given form_id could not be found.")
        except Question.DoesNotExist:
            raise NotFound(detail="A Question with the given question_id could not be found.")
        except IntegrityError:
            raise ValidationError({'position': f'An Option from Question {question_id} is already taking this position.'})
        

class OptionDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    View to get, modify or delete an existing Option
    from a given Question and Form.
    """

    serializer_class = OptionSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg =  'option_id'

    # Return a diferent QuerySet depending on the Option id 
    # used in the request.
    def get_queryset(self):
        form_id = self.kwargs.get('form_id')
        question_id = self.kwargs.get('question_id')
        option_id = self.kwargs.get('option_id')

        # Confirm if form_id and question_id were provided.
        if not form_id:
            raise ValidationError({'form_id': 'Missing URL parameter.'})
        if not question_id:
            raise ValidationError({'question_id': 'Missing URL parameter.'})
        
        print("[Successfully retrieved id's]")
        
        # Check if the Form with the given form_id exists.
        try:
            form = Form.objects.get(pk=form_id, created_by=self.request.user)
        except Form.DoesNotExist:
            raise NotFound(detail="A Form with the given form_id could not be found.")
        
        # Check if the Question with the given Form and question_id exists.
        try:
            question = Question.objects.get(pk=question_id, form=form)
        except Question.DoesNotExist:
            raise NotFound(detail="A Question with the given question_id could not be found.")
        
        print("[Successfully retrieved Form and Question objects]")

        # Check if the Option from the given Question and Form exists.
        option_queryset = Option.objects.all().filter(pk=option_id, question=question)
        if not option_queryset:
            raise NotFound(detail="An Option with the given option_id could not be found.")
        
        print("[Successfully returning queryset]")

        # Return the queryset with the Option found.
        return option_queryset
    
    # Override perform_destroy to update the 'date_updated' field from
    # the Question's Form before deleting the Option.
    def perform_destroy(self, instance):
        form = instance.question.form
        form.update_date_updated()
        return super().perform_destroy(instance)