# web/views.py
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView
from django.views.generic.base import View
from django.urls import reverse_lazy
from django.db.models import Avg, Count
from django.contrib import messages

from .forms import UserRegisterForm, CourseForm, VideoForm, RatingForm,CategoryForm
from api.models import User, Category, Course, Video, Enrollment, Rating, ViewedVideo


# Autentifikatsiya views'lari
def register_request(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz!')
            if user.role == 'student':
                # Talaba profiliga yo'naltirish
                return redirect('student_profile')
            elif user.role == 'teacher':
                # O'qituvchi dashboardiga yo'naltirish
                return redirect('teacher_dashboard')
            elif user.role == 'admin':
                # Admin dashboardiga yo'naltirish
                return redirect('admin_dashboard')

            # Agar yuqoridagi rollardan biri bo'lmasa, bosh sahifaga yo'naltirish
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'Xush kelibsiz, {username}!')
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'teacher':
                    return redirect('teacher_dashboard')
                elif user.role == 'student':
                    return redirect('student_profile')
            else:
                messages.error(request, 'Noto\'g\'ri foydalanuvchi nomi yoki parol.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_request(request):
    logout(request)
    messages.info(request, 'Tizimdan chiqdingiz.')
    return redirect('home')


#admin ucun viewslarr
class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'admin'

    def get(self, request):
        context = {
            'total_teachers': User.objects.filter(role='teacher').count(),
            'total_students': User.objects.filter(role='student').count(),
            'total_courses': Course.objects.count(),
            'teachers': User.objects.filter(role='teacher'),
            'students': User.objects.filter(role='student'),
        }
        return render(request, 'admin/dashboard.html', context)


class CategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Category
    template_name = 'admin/category_list.html'
    context_object_name = 'categories'

    def test_func(self):
        return self.request.user.role == 'admin'


# Techer ucun viewslaa
class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = 'teacher/dashboard.html'
    context_object_name = 'courses'

    def test_func(self):
        return self.request.user.role == 'teacher'

    def get_queryset(self):
        return Course.objects.filter(teacher=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        courses = self.get_queryset()
        for course in courses:
            course.students_count = Enrollment.objects.filter(course=course).count()
            course.average_rating = Rating.objects.filter(course=course).aggregate(avg_rating=Avg('rating'))[
                'avg_rating']
        context['courses'] = courses
        return context


class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'teacher/course_create.html'
    success_url = reverse_lazy('teacher_dashboard')

    def test_func(self):
        return self.request.user.role == 'teacher'

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        messages.success(self.request, 'Kurs muvaffaqiyatli yaratildi.')
        return super().form_valid(form)


class VideoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Video
    form_class = VideoForm
    template_name = 'teacher/video_create.html'

    def test_func(self):
        return self.request.user.role == 'teacher'

    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'pk': self.kwargs['course_id']})

    def form_valid(self, form):
        course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        if course.teacher != self.request.user:
            messages.error(self.request, 'Siz bu kursga video yuklay olmaysiz.')
            return self.form_invalid(form)

        form.instance.course = course
        messages.success(self.request, 'Video muvaffaqiyatli yuklandi.')
        return super().form_valid(form)


#Studentni viewslari
class StudentProfileView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'student/profile.html'

    def test_func(self):
        return self.request.user.role == 'student'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrolled_courses = Enrollment.objects.filter(student=self.request.user).select_related('course',
                                                                                               'course__teacher')

        course_data = []
        for enrollment in enrolled_courses:
            course = enrollment.course
            viewed_videos_count = ViewedVideo.objects.filter(student=self.request.user, video__course=course).count()
            total_videos_count = Video.objects.filter(course=course).count()

            course_data.append({
                'course': course,
                'teacher_name': course.teacher.username,
                'viewed_count': viewed_videos_count,
                'total_videos': total_videos_count,
            })

        context['enrolled_courses'] = course_data
        return context


class CourseListView(ListView):
    model = Course
    template_name = 'course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.kwargs.get('slug')
        if category_slug:
            # Agar URL'da slug mavjud bo'lsa, kurslarni kategoriya bo'yicha filtrlash
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Barcha kategoriyalarni sahifaga yuborish
        context['categories'] = Category.objects.all()
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = 'course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        context['videos'] = course.videos.all()
        context['rating_form'] = RatingForm()
        rating_data = Rating.objects.filter(course=course).aggregate(avg_rating=Avg('rating'))
        context['average_rating'] = rating_data.get('avg_rating', None)
        is_enrolled = False
        if self.request.user.is_authenticated and self.request.user.role == 'student':
            is_enrolled = Enrollment.objects.filter(student=self.request.user, course=course).exists()

        context['is_enrolled'] = is_enrolled
        return context

class EnrollCourseView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'student'

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        Enrollment.objects.get_or_create(student=request.user, course=course)
        messages.success(request, 'Kursga muvaffaqiyatli yozildingiz!')
        return redirect('course_detail', pk=pk)


class ViewVideoView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'student'

    def get(self, request, video_id):
        video = get_object_or_404(Video, pk=video_id)
        if not Enrollment.objects.filter(student=request.user, course=video.course).exists():
            messages.error(request, 'Bu videoni ko\'rish uchun avval kursga yoziling.')
            return redirect('course_detail', pk=video.course.id)

        ViewedVideo.objects.get_or_create(student=request.user, video=video)
        return render(request, 'video_player.html', {'video': video})


class RateCourseView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'student'

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.cleaned_data['rating']
            comment = form.cleaned_data.get('comment', '')
            Rating.objects.update_or_create(
                student=request.user,
                course=course,
                defaults={'rating': rating, 'comment': comment}
            )
            messages.success(request, 'Bahoyingiz qabul qilindi!')
        else:
            messages.error(request, 'Baho berishda xatolik yuz berdi.')
        return redirect('course_detail', pk=pk)

class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'admin/category_create.html'
    success_url = reverse_lazy('admin_dashboard')  # yoki boshqa URL nomi
    success_message = "Yangi kategoriya muvaffaqiyatli qo'shildi!"

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'admin'

    def form_valid(self, form):
        return super().form_valid(form)