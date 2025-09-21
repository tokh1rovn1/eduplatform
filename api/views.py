# api/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404

from .models import User, Category, Course, Video, Enrollment, Rating, ViewedVideo
from .serializers import (
    UserRegistrationSerializer, CategorySerializer, CourseSerializer,
    VideoSerializer, EnrollmentSerializer, StudentProfileSerializer, RatingSerializer
)
from .permissions import IsAdmin, IsTeacher, IsStudent


# Ro'yxatdan o'tish
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (permissions.AllowAny,)


# ---
## Admin API'lari
class AdminDashboardView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        data = {
            'total_teachers': User.objects.filter(role='teacher').count(),
            'total_students': User.objects.filter(role='student').count(),
            'total_courses': Course.objects.count(),
            'most_popular_courses': Course.objects.annotate(num_students=Count('enrollment')).order_by('-num_students')[
                :5].values('title', 'num_students'),
        }
        return Response(data)


class AdminCategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdmin]


class TeacherListAPIView(generics.ListAPIView):
    queryset = User.objects.filter(role='teacher')
    serializer_class = UserRegistrationSerializer  # Maxsus serializer ishlatish tavsiya qilinadi
    permission_classes = [IsAdmin]


class StudentListAPIView(generics.ListAPIView):
    queryset = User.objects.filter(role='student')
    serializer_class = UserRegistrationSerializer  # Maxsus serializer ishlatish tavsiya qilinadi
    permission_classes = [IsAdmin]


# ---
## Teacher API'lari
class TeacherDashboardView(APIView):
    permission_classes = [IsTeacher]

    def get(self, request):
        courses = Course.objects.filter(teacher=request.user)
        course_data = []
        for course in courses:
            students_count = Enrollment.objects.filter(course=course).count()
            average_rating = Rating.objects.filter(course=course).aggregate(avg_rating=Avg('rating'))['avg_rating']
            course_data.append({
                'title': course.title,
                'students_count': students_count,
                'average_rating': round(average_rating, 2) if average_rating else 'No ratings yet',
            })
        return Response({'my_courses': course_data})


class TeacherCourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Course.objects.filter(teacher=self.request.user)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class CourseVideoCreateView(generics.CreateAPIView):
    serializer_class = VideoSerializer
    permission_classes = [IsTeacher]

    def create(self, request, *args, **kwargs):
        course = get_object_or_404(Course, pk=self.kwargs.get('course_id'))

        if course.teacher != self.request.user:
            return Response({'error': 'You do not have permission to add videos to this course.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ---
## Student va Umumiy API'lar
class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]


class CourseEnrollmentView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)

        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({'error': 'You are already enrolled in this course.'}, status=status.HTTP_400_BAD_REQUEST)

        Enrollment.objects.create(student=request.user, course=course)
        return Response({'message': 'Successfully enrolled in the course.'}, status=status.HTTP_201_CREATED)


class StudentProfileView(generics.RetrieveAPIView):
    permission_classes = [IsStudent]
    serializer_class = StudentProfileSerializer

    def get_object(self):
        return self.request.user


class CourseRatingView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        serializer = RatingSerializer(data=request.data)

        if serializer.is_valid():
            # Agar oldin baho bergan bo'lsa, o'zgartirish uchun
            rating_instance, created = Rating.objects.get_or_create(
                student=request.user,
                course=course,
                defaults={'rating': serializer.validated_data['rating']}
            )
            if not created:
                rating_instance.rating = serializer.validated_data['rating']
                rating_instance.comment = serializer.validated_data.get('comment')
                rating_instance.save()

            return Response({'message': 'Rating submitted successfully.'},
                            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)