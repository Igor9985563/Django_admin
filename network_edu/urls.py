from django.urls import path
from . import views
from .views import (
    CourseListView, CourseDetailView, CourseCreateView,
    CourseUpdateView, CourseDeleteView, LessonDetailView, LessonListView
)

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', CourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('courses/new/', CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/update/', CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', CourseDeleteView.as_view(), name='course_delete'),
    path('courses/<int:pk>/enroll/', views.enroll_course, name='enroll_course'),
    path('courses/<int:pk>/unenroll/', views.unenroll_course, name='unenroll_course'),
    path('courses/<int:course_id>/review/', views.submit_review, name='submit_review'),

    path('courses/<int:course_id>/modules/new/', views.module_create, name='module_create'),
    path('modules/<int:module_id>/lessons/new/', views.lesson_create, name='lesson_create'),
    path('lessons/', LessonListView.as_view(), name='lessons'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson_detail'),
    path('lessons/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    path('lessons/<int:lesson_id>/incomplete/', views.mark_lesson_incomplete, name='mark_lesson_incomplete'),
    path('lessons/<int:lesson_id>/assignments/new/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:assignment_id>/submit/', views.submission_create, name='submission_create'),
    path('submissions/<int:submission_id>/review/', views.review_submission, name='review_submission'),

    path('resources/', views.resource_list, name='resource_list'),
    path('resources/new/', views.resource_create, name='resource_create'),

    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/edit/', views.profile_edit, name='profile_edit'),

    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

    # Новые URL для улучшения функционала
    path('certificate/<uuid:certificate_id>/', views.view_certificate, name='view_certificate'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('faq/', views.faq_list, name='faq'),
    path('search/', views.search, name='search'),  # Исправлено с search_view на search
    path('calendar/', views.calendar, name='calendar'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),

]
