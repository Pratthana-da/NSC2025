# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid
import secrets
import string

class User(AbstractUser):
    USER_TYPES = (
        ('student', 'นักเรียน'),
        ('teacher', 'ครู'),
        ('admin', 'ผู้ดูแลระบบ'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')
    email = models.EmailField(unique=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    # models.py (User class)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    line = models.CharField(max_length=100, blank=True, null=True)
    teaching_subjects = models.CharField(max_length=200, blank=True, null=True)
    class_code = models.CharField(max_length=50, blank=True, null=True)
    classroom_link = models.URLField(blank=True, null=True)

    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

class Classroom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='ชื่อวิชา')
    code = models.CharField(max_length=10, unique=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_classes')
    students = models.ManyToManyField(User, related_name='enrolled_classes', blank=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_classes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)
    
    def generate_unique_code(self):
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not Classroom.objects.filter(code=code).exists():
                return code


# classroom/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Lesson(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="lessons", null=True, blank=True)  # ✅ เพิ่ม
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='lessons/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    


# models.py
class Storybook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="storybooks", null=True, blank=True)  # ✅ เพิ่ม
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='lessons/')
    created_at = models.DateTimeField(auto_now_add=True)
    is_ready = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)

class Scene(models.Model):
    storybook = models.ForeignKey(Storybook, related_name='scenes', on_delete=models.CASCADE)
    scene_number = models.PositiveIntegerField()
    text = models.TextField()
    image_prompt = models.TextField()
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    audio_url = models.URLField(max_length=1000, blank=True, null=True)  # ✅ เพิ่ม




