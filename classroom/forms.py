# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User
from django.utils import timezone
import re

class SecureUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    user_type = forms.ChoiceField(choices=[('teacher', 'Teacher'), ('student', 'Student')],widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("อีเมลนี้ถูกใช้งานแล้ว")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("ชื่อผู้ใช้ต้องมีเฉพาะตัวอักษร ตัวเลข และ underscore เท่านั้น")
        return username

class SecureAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'อีเมล'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'รหัสผ่าน'}))
    
    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                
                # Check if account is locked
                if user.account_locked_until and user.account_locked_until > timezone.now():
                    raise ValidationError("บัญชีถูกล็อก กรุณาลองใหม่ภายหลัง")
                
                # Check if user is approved
                # ✅ เฉพาะครูเท่านั้นที่ต้องรออนุมัติ
                if user.user_type == 'teacher' and not user.is_approved:
                    raise ValidationError("บัญชีครูยังไม่ได้รับการอนุมัติจากผู้ดูแลระบบ")

                self.user_cache = authenticate(self.request, username=email, password=password)
                if self.user_cache is None:
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 5:
                        user.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)
                    user.save()
                    raise ValidationError("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
                else:
                    user.failed_login_attempts = 0
                    user.account_locked_until = None
                    user.save()
            except User.DoesNotExist:
                raise ValidationError("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
        
        return self.cleaned_data


class JoinClassroomForm(forms.Form):
    classroom_code = forms.CharField(
        max_length=10, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'รหัสชั้นเรียน'})
    )