# api/serializers.py
from rest_framework import serializers
from .models import User, Category, Course, Video, Enrollment, Rating, ViewedVideo


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'role')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data.get('role', 'student')
        )
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Course
        fields = '__all__'


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Enrollment
        fields = '__all__'


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ('rating', 'comment')


class StudentProfileSerializer(serializers.ModelSerializer):
    enrolled_courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'enrolled_courses')

    def get_enrolled_courses(self, obj):
        enrollments = Enrollment.objects.filter(student=obj).select_related('course', 'course__teacher')
        course_list = []
        for enrollment in enrollments:
            course = enrollment.course
            viewed_videos_count = ViewedVideo.objects.filter(student=obj, video__course=course).count()
            total_videos_count = course.videos.count()

            course_data = {
                'id': course.id,
                'title': course.title,
                'teacher_name': course.teacher.username,
                'viewed_videos': f'{viewed_videos_count}/{total_videos_count}',
            }
            course_list.append(course_data)
        return course_list