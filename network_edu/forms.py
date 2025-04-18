from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Course, Module, Lesson, Assignment, Submission, Resource, Profile, CourseReview, FAQ, Category, Project


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Электронная почта')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Имя пользователя',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']
        labels = {
            'bio': 'О себе',
            'avatar': 'Аватар',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class CombinedRegisterForm(UserRegisterForm):
    bio = forms.CharField(
        label='О себе',
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False
    )
    avatar = forms.ImageField(label='Аватар', required=False)

    class Meta(UserRegisterForm.Meta):
        fields = UserRegisterForm.Meta.fields + ['bio', 'avatar']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'image', 'is_active']
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'category': 'Категория',
            'image': 'Изображение',
            'is_active': 'Активен',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description']
        labels = {
            'title': 'Название модуля',
            'description': 'Описание модуля',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content']
        labels = {
            'title': 'Название урока',
            'content': 'Содержание',
        }


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'points']
        labels = {
            'title': 'Название задания',
            'description': 'Описание',
            'due_date': 'Срок сдачи',
            'points': 'Баллы',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['content', 'file']
        labels = {
            'content': 'Комментарий к работе',
            'file': 'Файл',
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'file']
        labels = {
            'title': 'Название ресурса',
            'description': 'Описание',
            'file': 'Файл',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CourseReviewForm(forms.ModelForm):
    class Meta:
        model = CourseReview
        fields = ['rating', 'comment']
        labels = {
            'rating': 'Оценка',
            'comment': 'Комментарий',
        }
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Поделитесь своим мнением о курсе...'}),
        }


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'order', 'is_active']
        labels = {
            'question': 'Вопрос',
            'answer': 'Ответ',
            'order': 'Порядок',
            'is_active': 'Активен',
        }


class SearchForm(forms.Form):
    query = forms.CharField(
        label='Поиск',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Поиск по курсам, урокам и ресурсам...',
            'class': 'form-control'
        })
    )

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'file']