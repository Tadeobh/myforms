from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # User and Session Management
    path('', include(router.urls)),
    path('login/', views.MyTokenObtainPairView.as_view(), name='login'),

    # Forms
    path('forms/', views.FormList.as_view(), name='forms_list'),
    path('forms/<int:pk>/', views.FormDetail.as_view(), name='form_detail'),

    # Questions
    path('forms/<int:form_id>/questions/', views.QuestionList.as_view(), name='questions_list'),
    path('forms/<int:form_id>/questions/<int:question_id>/', views.QuestionDetail.as_view(), name='question_detail'),

    # Options
    path('forms/<int:form_id>/questions/<int:question_id>/options/', views.OptionList.as_view(), name='options_list'),
    path('forms/<int:form_id>/questions/<int:question_id>/options/<int:option_id>/', views.OptionDetail.as_view(), 
         name='option_detail'),

    # Response
    path('forms/<int:form_id>/responses/', views.ResponseList.as_view(), name='responses_list'),
    path('forms/<int:form_id>/responses/<int:response_id>/', views.ResponseDetail.as_view(), name='response_detail'),
]