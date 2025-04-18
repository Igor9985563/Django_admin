from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Avg
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import (
    Module, Lesson, Assignment, Submission, Resource,
    Enrollment, CourseProgress, Certificate, CourseReview,
    Notification, FAQ
)
from .forms import (
    CourseForm, ModuleForm, LessonForm, AssignmentForm, SubmissionForm,
    ResourceForm, ProfileForm, CourseReviewForm, SearchForm
)
from django.http import HttpResponseForbidden
from django.db.models import Q
from .models import Course, Category
from django.shortcuts import render, redirect, get_object_or_404
from .models import Project
from .forms import ProjectForm
from django.contrib.auth.decorators import login_required



def home(request):
    courses = Course.objects.filter(is_active=True)[:3]
    return render(request, 'network_edu/home.html', {'courses': courses})


class CourseListView(ListView):
    model = Course
    template_name = 'network_edu/course_list.html'
    context_object_name = 'courses'
    paginate_by = 6

    def get_queryset(self):
        query = self.request.GET.get('q')
        category_id = self.request.GET.get('category')
        qs = Course.objects.filter(is_active=True)

        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )

        if category_id:
            qs = qs.filter(category_id=category_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category')
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = 'network_edu/course_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user,
                course=self.object,
                is_active=True
            ).exists()

            # Проверяем, оставил ли пользователь отзыв
            context['user_review'] = CourseReview.objects.filter(
                student=self.request.user,
                course=self.object
            ).first()

            # Форма для отзыва
            context['review_form'] = CourseReviewForm(instance=context['user_review'])

        # Добавляем подсчет активных записей на курс
        context['active_enrollments_count'] = Enrollment.objects.filter(
            course=self.object,
            is_active=True
        ).count()

        # Добавляем отзывы о курсе
        context['reviews'] = CourseReview.objects.filter(course=self.object).order_by('-created_at')

        # Средний рейтинг курса
        avg_rating = CourseReview.objects.filter(course=self.object).aggregate(Avg('rating'))
        context['avg_rating'] = avg_rating['rating__avg'] or 0

        # Количество отзывов
        context['review_count'] = CourseReview.objects.filter(course=self.object).count()

        return context


@login_required
def enroll_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        enrollment.is_active = True
        enrollment.save()
        messages.success(request, f'Вы успешно восстановлены на курс {course.title}')
    else:
        Enrollment.objects.create(student=request.user, course=course)

        # Создаем уведомление для инструктора
        Notification.objects.create(
            user=course.instructor,
            title='Новый студент на курсе',
            message=f'Пользователь {request.user.username} записался на ваш курс "{course.title}"',
            notification_type='enrollment',
            related_link=f'/courses/{course.id}/'
        )

        messages.success(request, f'Вы успешно записались на курс {course.title}')
    return redirect('course_detail', pk=course.pk)


@login_required
def unenroll_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    enrollment.is_active = False
    enrollment.save()
    messages.success(request, f'Вы успешно отписались от курса {course.title}')
    return redirect('course_detail', pk=course.pk)


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'network_edu/lesson_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object
        module = lesson.module
        course = module.course

        # Check if user is enrolled
        is_enrolled = Enrollment.objects.filter(
            student=self.request.user,
            course=course,
            is_active=True
        ).exists()

        if not is_enrolled and not self.request.user.profile.is_instructor:
            messages.error(self.request, 'Вы должны быть записаны на курс для просмотра уроков')
            return context

        context['module'] = module
        context['course'] = course
        context['assignments'] = lesson.assignments.all()

        # Get next and previous lessons
        lessons = list(module.lessons.all())
        current_index = lessons.index(lesson)

        if current_index > 0:
            context['prev_lesson'] = lessons[current_index - 1]

        if current_index < len(lessons) - 1:
            context['next_lesson'] = lessons[current_index + 1]

        # Отслеживание прогресса
        progress, created = CourseProgress.objects.get_or_create(
            student=self.request.user,
            lesson=lesson
        )
        progress.last_accessed = timezone.now()
        progress.save()

        # Получаем прогресс по курсу
        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_lessons = CourseProgress.objects.filter(
            student=self.request.user,
            lesson__module__course=course,
            completed=True
        ).count()

        if total_lessons > 0:
            context['progress_percent'] = int((completed_lessons / total_lessons) * 100)
        else:
            context['progress_percent'] = 0

        context['is_completed'] = progress.completed

        return context

class LessonListView(ListView):
    model = Lesson
    template_name = 'network_edu/lesson_list.html'
    context_object_name = 'lessons'
    paginate_by = 10

@login_required
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    progress, created = CourseProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )
    progress.completed = True
    progress.save()

    # Проверяем, завершил ли студент все уроки курса
    course = lesson.module.course
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = CourseProgress.objects.filter(
        student=request.user,
        lesson__module__course=course,
        completed=True
    ).count()

    # Если все уроки завершены, создаем сертификат
    if total_lessons > 0 and total_lessons == completed_lessons:
        certificate, created = Certificate.objects.get_or_create(
            student=request.user,
            course=course
        )
        if created:
            messages.success(request, f'Поздравляем! Вы завершили курс "{course.title}" и получили сертификат.')

    messages.success(request, 'Урок отмечен как завершенный')
    return redirect('lesson_detail', pk=lesson_id)


@login_required
def mark_lesson_incomplete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    progress = get_object_or_404(CourseProgress, student=request.user, lesson=lesson)
    progress.completed = False
    progress.save()

    messages.success(request, 'Урок отмечен как незавершенный')
    return redirect('lesson_detail', pk=lesson_id)


class InstructorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'profile') and self.request.user.profile.is_instructor


class CourseCreateView(InstructorRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'network_edu/course_form.html'

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)


class CourseUpdateView(InstructorRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'network_edu/course_form.html'

    def test_func(self):
        course = self.get_object()
        return super().test_func() and course.instructor == self.request.user


class CourseDeleteView(InstructorRequiredMixin, DeleteView):
    model = Course
    template_name = 'network_edu/course_confirm_delete.html'
    success_url = reverse_lazy('course_list')

    def test_func(self):
        course = self.get_object()
        return super().test_func() and course.instructor == self.request.user


@login_required
def module_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not request.user.profile.is_instructor or course.instructor != request.user:
        messages.error(request, 'У вас нет прав для создания модулей в этом курсе')
        return redirect('course_detail', pk=course.pk)

    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.order = course.modules.count() + 1
            module.save()
            messages.success(request, 'Модуль успешно создан')
            return redirect('course_detail', pk=course.pk)
    else:
        form = ModuleForm()

    return render(request, 'network_edu/module_form.html', {'form': form, 'course': course})


@login_required
def lesson_create(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    if not request.user.profile.is_instructor or course.instructor != request.user:
        messages.error(request, 'У вас нет прав для создания уроков в этом модуле')
        return redirect('course_detail', pk=course.pk)

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.order = module.lessons.count() + 1
            lesson.save()

            # Создаем уведомления для всех студентов курса
            enrollments = Enrollment.objects.filter(course=course, is_active=True)
            for enrollment in enrollments:
                Notification.objects.create(
                    user=enrollment.student,
                    title='Новый урок доступен',
                    message=f'В курсе "{course.title}" добавлен новый урок: "{lesson.title}"',
                    notification_type='assignment',
                    related_link=f'/lessons/{lesson.id}/'
                )

            messages.success(request, 'Урок успешно создан')
            return redirect('lesson_detail', pk=lesson.pk)
    else:
        form = LessonForm()

    return render(request, 'network_edu/lesson_form.html', {'form': form, 'module': module, 'course': course})


@login_required
def assignment_create(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    module = lesson.module
    course = module.course

    if not request.user.profile.is_instructor or course.instructor != request.user:
        messages.error(request, 'У вас нет прав для создания заданий в этом уроке')
        return redirect('lesson_detail', pk=lesson.pk)

    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.lesson = lesson
            assignment.save()

            # Создаем уведомления для всех студентов курса
            enrollments = Enrollment.objects.filter(course=course, is_active=True)
            for enrollment in enrollments:
                Notification.objects.create(
                    user=enrollment.student,
                    title='Новое задание',
                    message=f'В уроке "{lesson.title}" добавлено новое задание: "{assignment.title}"',
                    notification_type='assignment',
                    related_link=f'/lessons/{lesson.id}/'
                )

            messages.success(request, 'Задание успешно создано')
            return redirect('lesson_detail', pk=lesson.pk)
    else:
        form = AssignmentForm()

    return render(request, 'network_edu/assignment_form.html', {
        'form': form,
        'lesson': lesson,
        'module': module,
        'course': course
    })


@login_required
def submission_create(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    lesson = assignment.lesson
    module = lesson.module
    course = module.course

    # Check if user is enrolled
    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).exists()

    if not is_enrolled:
        messages.error(request, 'Вы должны быть записаны на курс для отправки решений')
        return redirect('course_detail', pk=course.pk)

    # Check if user already submitted
    existing_submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, instance=existing_submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.status = 'pending'
            submission.save()

            # Создаем уведомление для инструктора
            Notification.objects.create(
                user=course.instructor,
                title='Новое решение на проверку',
                message=f'Студент {request.user.username} отправил решение для задания "{assignment.title}"',
                notification_type='assignment',
                related_link=f'/submissions/{submission.id}/review/'
            )

            messages.success(request, 'Решение успешно отправлено')
            return redirect('lesson_detail', pk=lesson.pk)
    else:
        form = SubmissionForm(instance=existing_submission)

    return render(request, 'network_edu/submission_form.html', {
        'form': form,
        'assignment': assignment,
        'lesson': lesson,
        'existing_submission': existing_submission
    })


@login_required
def review_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    assignment = submission.assignment
    lesson = assignment.lesson
    module = lesson.module
    course = module.course

    if not request.user.profile.is_instructor or course.instructor != request.user:
        messages.error(request, 'У вас нет прав для проверки этого решения')
        return redirect('home')

    if request.method == 'POST':
        status = request.POST.get('status')
        feedback = request.POST.get('feedback')
        score = request.POST.get('score')

        submission.status = status
        submission.feedback = feedback
        if score:
            submission.score = int(score)
        submission.save()

        # Создаем уведомление для студента
        Notification.objects.create(
            user=submission.student,
            title='Ваше решение проверено',
            message=f'Инструктор проверил ваше решение для задания "{assignment.title}"',
            notification_type='feedback',
            related_link=f'/lessons/{lesson.id}/'
        )

        messages.success(request, 'Решение успешно проверено')
        return redirect('instructor_dashboard')

    return render(request, 'network_edu/review_submission.html', {'submission': submission})


@login_required
def resource_list(request):
    resources = Resource.objects.all().order_by('-uploaded_at')
    return render(request, 'network_edu/resource_list.html', {'resources': resources})


@login_required
def resource_create(request):
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, 'Ресурс успешно добавлен')
            return redirect('resource_list')
    else:
        form = ResourceForm()

    return render(request, 'network_edu/resource_form.html', {'form': form})


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'network_edu/profile.html', {'profile_user': user})


@login_required
def profile_edit(request, username):
    if request.user.username != username:
        return HttpResponseForbidden("Нельзя редактировать чужой профиль")

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'network_edu/profile_edit.html', {'form': form, 'user': request.user})


@login_required
def instructor_dashboard(request):
    if not request.user.profile.is_instructor:
        messages.error(request, 'У вас нет прав для доступа к панели инструктора')
        return redirect('home')

    courses = Course.objects.filter(instructor=request.user)

    # Добавляем количество активных студентов для каждого курса
    for course in courses:
        course.active_students_count = Enrollment.objects.filter(
            course=course,
            is_active=True
        ).count()

    pending_submissions = Submission.objects.filter(
        assignment__lesson__module__course__instructor=request.user,
        status='pending'
    )

    # Добавляем статистику
    total_students = Enrollment.objects.filter(
        course__instructor=request.user,
        is_active=True
    ).values('student').distinct().count()

    total_lessons = Lesson.objects.filter(
        module__course__instructor=request.user
    ).count()

    return render(request, 'network_edu/instructor_dashboard.html', {
        'courses': courses,
        'pending_submissions': pending_submissions,
        'total_students': total_students,
        'total_lessons': total_lessons
    })


@login_required
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(student=request.user, is_active=True)
    submissions = Submission.objects.filter(student=request.user).order_by('-submitted_at')

    # Добавляем прогресс по курсам
    courses_progress = []
    for enrollment in enrollments:
        course = enrollment.course
        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_lessons = CourseProgress.objects.filter(
            student=request.user,
            lesson__module__course=course,
            completed=True
        ).count()

        if total_lessons > 0:
            progress_percent = int((completed_lessons / total_lessons) * 100)
        else:
            progress_percent = 0

        courses_progress.append({
            'course': course,
            'progress_percent': progress_percent,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons
        })

    # Получаем сертификаты пользователя
    certificates = Certificate.objects.filter(student=request.user)

    # Получаем уведомления пользователя
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]

    return render(request, 'network_edu/student_dashboard.html', {
        'enrollments': enrollments,
        'submissions': submissions,
        'courses_progress': courses_progress,
        'certificates': certificates,
        'notifications': notifications
    })


# Новые представления для улучшения функционала

@login_required
def submit_review(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Проверяем, записан ли пользователь на курс
    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).exists()

    if not is_enrolled:
        messages.error(request, 'Вы должны быть записаны на курс, чтобы оставить отзыв')
        return redirect('course_detail', pk=course_id)

    # Проверяем, существует ли уже отзыв
    review = CourseReview.objects.filter(student=request.user, course=course).first()

    if request.method == 'POST':
        form = CourseReviewForm(request.POST, instance=review)
        if form.is_valid():
            new_review = form.save(commit=False)
            new_review.student = request.user
            new_review.course = course
            new_review.save()

            # Создаем уведомление для инструктора
            Notification.objects.create(
                user=course.instructor,
                title='Новый отзыв о курсе',
                message=f'Пользователь {request.user.username} оставил отзыв о курсе "{course.title}"',
                notification_type='feedback',
                related_link=f'/courses/{course.id}/'
            )

            messages.success(request, 'Ваш отзыв успешно сохранен')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')

    return redirect('course_detail', pk=course_id)


@login_required
def view_certificate(request, certificate_id):
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)

    # Проверяем, принадлежит ли сертификат пользователю или является ли пользователь инструктором курса
    if certificate.student != request.user and certificate.course.instructor != request.user:
        messages.error(request, 'У вас нет доступа к этому сертификату')
        return redirect('home')

    return render(request, 'network_edu/certificate.html', {'certificate': certificate})


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    # Если есть связанная ссылка, перенаправляем на нее
    if notification.related_link:
        return redirect(notification.related_link)

    return redirect('notifications')


@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Отмечаем все уведомления как прочитанные
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        notifications.update(is_read=True)
        messages.success(request, 'Все уведомления отмечены как прочитанные')
        return redirect('notifications')

    return render(request, 'network_edu/notifications.html', {'notifications': notifications})


def faq_list(request):
    faqs = FAQ.objects.filter(is_active=True).order_by('order')
    return render(request, 'network_edu/faq.html', {'faqs': faqs})


@login_required
def search(request):
    form = SearchForm(request.GET)
    results = {'courses': [], 'lessons': [], 'resources': []}

    if form.is_valid() and form.cleaned_data['query']:
        query = form.cleaned_data['query']

        # Поиск по курсам
        results['courses'] = Course.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).filter(is_active=True)

        # Поиск по урокам
        results['lessons'] = Lesson.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )

        # Поиск по ресурсам
        results['resources'] = Resource.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'network_edu/search_results.html', {
        'form': form,
        'results': results,
        'query': form.cleaned_data.get('query', '')
    })


@login_required
def calendar(request):
    # Получаем все курсы, на которые записан пользователь
    enrollments = Enrollment.objects.filter(student=request.user, is_active=True)
    courses = [enrollment.course for enrollment in enrollments]

    # Получаем все задания с дедлайнами для этих курсов
    assignments = Assignment.objects.filter(
        lesson__module__course__in=courses,
        due_date__isnull=False
    ).order_by('due_date')

    # Группируем задания по месяцам
    upcoming_assignments = []
    for assignment in assignments:
        if assignment.due_date > timezone.now():
            upcoming_assignments.append(assignment)

    # Получаем задания с истекающим сроком сдачи (в течение 3 дней)
    deadline_soon = []
    for assignment in upcoming_assignments:
        if assignment.due_date - timezone.now() <= timedelta(days=3):
            deadline_soon.append(assignment)

    return render(request, 'network_edu/calendar.html', {
        'assignments': assignments,
        'upcoming_assignments': upcoming_assignments,
        'deadline_soon': deadline_soon
    })


def about(request):
    return render(request, 'network_edu/about.html')


def contact(request):
    return render(request, 'network_edu/contact.html')


def project_list(request):
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'projects/project_list.html', {'projects': projects})

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.author = request.user
            project.save()
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form})

