# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserRegistrationView, AdminDashboardView, AdminCategoryListCreateView,
    TeacherListAPIView, StudentListAPIView, TeacherDashboardView,
    TeacherCourseListCreateView, CourseVideoCreateView, CourseListView,
    CourseEnrollmentView, StudentProfileView, CourseRatingView
)

urlpatterns = [
    # Autentifikatsiya va ro'yxatdan o'tish
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Admin yo'llari
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/categories/', AdminCategoryListCreateView.as_view(), name='admin-categories-list-create'),
    path('admin/teachers/', TeacherListAPIView.as_view(), name='admin-teachers-list'),
    path('admin/students/', StudentListAPIView.as_view(), name='admin-students-list'),

    # Teacher yo'llari
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher-dashboard'),
    path('teacher/courses/', TeacherCourseListCreateView.as_view(), name='teacher-courses-list-create'),
    path('teacher/courses/<int:course_id>/add/', CourseVideoCreateView.as_view(),
         name='teacher-course-video-create'),

    # Student va Umumiy yo'llar
    path('courses/', CourseListView.as_view(), name='courses-list'),
    path('courses/<int:course_id>/enroll/', CourseEnrollmentView.as_view(), name='course-enroll'),
    path('courses/<int:course_id>/rate/', CourseRatingView.as_view(), name='course-rate'),
    path('student/profile/', StudentProfileView.as_view(), name='student-profile'),
]