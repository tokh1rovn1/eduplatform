from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifa
    path('', views.CourseListView.as_view(), name='home'),

    # Kurslar ro'yxati va kategoriyalar bo'yicha filtrlash
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('categories/<str:slug>/', views.CourseListView.as_view(), name='courses_by_category'),

    # Kursning batafsil sahifasi
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),

    # Autentifikatsiya views'lari
    path('register/', views.register_request, name='register'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),

    # Admin
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/categories/', views.CategoryListView.as_view(), name='admin_categories'),
path('admin/category/create/', views.CategoryCreateView.as_view(), name='admin_category_create'),

    # Teacher
    path('teacher/dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('teacher/course/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('teacher/course/<int:course_id>/video/add/', views.VideoCreateView.as_view(), name='video_add'),

    # Student
    path('student/profile/', views.StudentProfileView.as_view(), name='student_profile'),
    path('courses/<int:pk>/enroll/', views.EnrollCourseView.as_view(), name='enroll_course'),
    path('courses/<int:pk>/rate/', views.RateCourseView.as_view(), name='rate_course'),
    path('video/<int:video_id>/', views.ViewVideoView.as_view(), name='view_video'),
]