from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify

from api.models import User, Course, Video, Rating, Category

class UserRegisterForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('role',)

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'video_file']

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Slugni nomdan avtomatik generatsiya qilish
        slug = slugify(self.cleaned_data['name'])

        # Dublikat nomlar uchun slugni noyob qilish
        original_slug = slug
        i = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f'{original_slug}-{i}'
            i += 1

        instance.slug = slug

        if commit:
            instance.save()
        return instance