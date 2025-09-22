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

# ---
## Authentication and Registration
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class MyTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


# ---
## Admin API'lari
class AdminDashboardView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = {
            'total_teachers': User.objects.filter(role='teacher').count(),
            'total_students': User.objects.filter(role='student').count(),
            'total_courses': Course.objects.count(),
            'most_popular_courses': Course.objects.annotate(
                num_students=Count('enrollment')
            ).order_by('-num_students')[:5].values('title', 'num_students'),
        }
        return Response(data)


class AdminCategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class TeacherListAPIView(generics.ListAPIView):
    queryset = User.objects.filter(role='teacher')
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class StudentListAPIView(generics.ListAPIView):
    queryset = User.objects.filter(role='student')
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


# ---
## Teacher API'lari
class TeacherDashboardView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        courses = Course.objects.filter(teacher=request.user) if request.user.is_authenticated else Course.objects.none()
        course_data = []
        for course in courses:
            students_count = Enrollment.objects.filter(course=course).count()
            average_rating = Rating.objects.filter(course=course).aggregate(
                avg_rating=Avg('rating')
            )['avg_rating']
            course_data.append({
                'title': course.title,
                'students_count': students_count,
                'average_rating': round(average_rating, 2) if average_rating else 'No ratings yet',
            })
        return Response({'my_courses': course_data})


class TeacherCourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Course.objects.filter(teacher=self.request.user)
        return Course.objects.none()

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user if self.request.user.is_authenticated else None)


class CourseVideoCreateView(generics.CreateAPIView):
    serializer_class = VideoSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        course = get_object_or_404(Course, pk=self.kwargs.get('course_id'))
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
    permission_classes = [permissions.AllowAny]

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)

        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({'error': 'You are already enrolled in this course.'}, status=400)

        Enrollment.objects.create(student=request.user if request.user.is_authenticated else None, course=course)
        return Response({'message': 'Successfully enrolled in the course.'}, status=201)


class StudentProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StudentProfileSerializer

    def get_object(self):
        return self.request.user if self.request.user.is_authenticated else None


class CourseRatingView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        serializer = RatingSerializer(data=request.data)

        if serializer.is_valid():
            rating_instance, created = Rating.objects.get_or_create(
                student=request.user if request.user.is_authenticated else None,
                course=course,
                defaults={'rating': serializer.validated_data['rating'],
                          'comment': serializer.validated_data.get('comment')}
            )
            if not created:
                rating_instance.rating = serializer.validated_data['rating']
                rating_instance.comment = serializer.validated_data.get('comment')
                rating_instance.save()

            return Response({'message': 'Rating submitted successfully.'},
                            status=201 if created else 200)

        return Response(serializer.errors, status=400)
