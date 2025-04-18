from django.contrib import admin
from .models import (
    Profile, Course, Module, Lesson, Assignment, Submission,
    Resource, Enrollment, CourseProgress, Certificate,
    CourseReview, Notification, FAQ, Category
)

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'category')
    search_fields = ('title', 'description', 'instructor__username')
    inlines = [ModuleInline]


class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order')
    list_filter = ('module__course',)
    search_fields = ('title', 'content')

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'due_date', 'points')
    list_filter = ('lesson__module__course',)
    search_fields = ('title', 'description')

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submitted_at', 'status', 'score')
    list_filter = ('status', 'submitted_at')
    search_fields = ('student__username', 'assignment__title', 'feedback')

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'is_active')
    list_filter = ('is_active', 'enrolled_at')
    search_fields = ('student__username', 'course__title')

class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'completed', 'last_accessed')
    list_filter = ('completed', 'last_accessed')
    search_fields = ('student__username', 'lesson__title')

class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'issue_date', 'certificate_id')
    list_filter = ('issue_date',)
    search_fields = ('student__username', 'course__title', 'certificate_id')
    readonly_fields = ('certificate_id',)

class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('student__username', 'course__title', 'comment')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')

class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')

admin.site.register(Profile)
admin.site.register(Course, CourseAdmin)
admin.site.register(Module)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Resource)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(CourseProgress, CourseProgressAdmin)
admin.site.register(Certificate, CertificateAdmin)
admin.site.register(CourseReview, CourseReviewAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(FAQ, FAQAdmin)
