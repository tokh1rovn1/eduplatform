# api/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Course, Video, Enrollment, Rating, ViewedVideo

# User modelini admin panelda ko'rsatish
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active',)
    list_filter = ('role', 'is_staff', 'is_active',)

# Boshqa modellarni admin panelda ro'yxatdan o'tkazish
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'created_at',)
    list_filter = ('teacher', 'category',)
    search_fields = ('title', 'teacher__username',)

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'course',)
    list_filter = ('course',)
    search_fields = ('title', 'course__title',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at',)
    list_filter = ('course', 'student',)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating',)
    list_filter = ('course', 'rating',)

@admin.register(ViewedVideo)
class ViewedVideoAdmin(admin.ModelAdmin):
    list_display = ('student', 'video', 'viewed_at',)
    list_filter = ('student', 'video',)