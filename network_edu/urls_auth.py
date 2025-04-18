from django.urls import path
from . import views_auth

urlpatterns = [
    path('register/', views_auth.register, name='register'),
]
