# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.utils import timezone
from django.db.models import Q
from .models import User, Classroom
from .forms import SecureUserCreationForm, SecureAuthenticationForm, JoinClassroomForm
import logging
from django.http import HttpResponse 
from django.shortcuts import redirect, render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ClassroomSerializer
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage

@login_required
def profile_settings(request):
    return render(request, 'profile_settings.html')

@login_required
def veiwe_profile(request):
    return render(request, 'veiwe_profile.html')

@api_view(['GET'])
def classroom_list_api(request):
    user = request.user
    if user.user_type == 'teacher':
        classrooms = Classroom.objects.filter(teacher=user)
    elif user.user_type == 'student':
        classrooms = user.enrolled_classes.all()
    else:
        classrooms = Classroom.objects.none()
    
    serializer = ClassroomSerializer(classrooms, many=True)
    return Response(serializer.data)


logger = logging.getLogger('django.security')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



@csrf_protect
@never_cache
def auth_view(request):
    if request.user.is_authenticated:
        return redirect('class_join_create')

    if request.method == 'POST':
        action = request.POST.get('action')
        print("🔍 action =", action)

        if action == 'login':
            form = SecureAuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                user.last_login_ip = get_client_ip(request)
                user.save()
                login(request, user)
                logger.info(f'User {user.email} logged in from IP {get_client_ip(request)}')
                messages.success(request, 'เข้าสู่ระบบสำเร็จ')

                # ✅ เงื่อนไขหลังล็อกอิน
                if user.user_type == 'student':
                    if user.enrolled_classes.exists():
                        return redirect('courses_enroll')
                    else:
                        return redirect('class_join_create')

                elif user.user_type == 'teacher':
                    return redirect('classroom_created')

                else:
                    return redirect('class_join_create')

            else:
                logger.warning(f'Failed login attempt from IP {get_client_ip(request)}')
                messages.error(request, 'เข้าสู่ระบบไม่สำเร็จ')

        elif action == 'register':
            form = SecureUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_approved = user.user_type in ['admin', 'student']
                user.save()
                logger.info(f'New user registered: {user.email} ({user.user_type})')
                if user.user_type in ['admin', 'student']:
                    login(request, user)
                    return redirect('class_join_create')
                else:
                    messages.success(request, 'สมัครสมาชิกสำเร็จ รอการอนุมัติจากผู้ดูแลระบบ')
                    return redirect('auth_view')
            else:
                print("❌ REGISTER FORM ERRORS:", form.errors)
                messages.error(request, 'เกิดข้อผิดพลาดในการสมัครสมาชิก')

    login_form = SecureAuthenticationForm()
    register_form = SecureUserCreationForm()

    return render(request, 'auth.html', {
        'login_form': login_form,
        'register_form': register_form
    })


@login_required
def dashboard(request):
    if request.user.user_type == 'teacher':
        classrooms = Classroom.objects.filter(teacher=request.user)
    elif request.user.user_type == 'student':
        classrooms = request.user.enrolled_classes.all()
    else:
        classrooms = Classroom.objects.none()

    return render(request, 'class_join_create.html', {
        'classrooms': classrooms
    })



@login_required
@never_cache
def dashboard_view(request):
    if request.user.user_type == 'admin':
        return redirect('admin_dashboard')
    
    return render(request, 'class_join_create.html', {
        'user': request.user,
        'classrooms': request.user.enrolled_classes.filter(is_approved=True) if request.user.user_type == 'student' else request.user.teaching_classes.filter(is_approved=True)
    })

@login_required
def admin_dashboard(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('class_join_create')
    
    pending_users = User.objects.filter(is_approved=False, user_type__in=['teacher', 'student'])
    pending_requests = ClassroomRequest.objects.filter(status='pending')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve_user':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            user.is_approved = True
            user.save()
            messages.success(request, f'อนุมัติบัญชี {user.email} แล้ว')
        
        elif action == 'approve_request':
            request_id = request.POST.get('request_id')
            classroom_request = get_object_or_404(ClassroomRequest, id=request_id)
            classroom_request.status = 'approved'
            classroom_request.reviewed_by = request.user
            classroom_request.reviewed_at = timezone.now()
            classroom_request.save()
            messages.success(request, f'อนุมัติการสร้างชั้นเรียน {classroom_request.subject_name} แล้ว')
    
    return render(request, 'admin_dashboard.html', {
        'pending_users': pending_users,
        'pending_requests': pending_requests
    })

@login_required
def create_classroom(request):
    if request.user.user_type != 'teacher':
        messages.error(request, 'เฉพาะครูเท่านั้นที่สามารถสร้างชั้นเรียนได้')
        return redirect('class_join_create')

    # ✅ ดึงชั้นเรียนที่ครูสร้างไว้แล้ว
    classrooms = Classroom.objects.filter(teacher=request.user)

    if request.method == 'POST':
        subject_name = request.POST.get('subject_name')
        if subject_name:
            classroom = Classroom.objects.create(
                name=subject_name,
                teacher=request.user,
                is_approved=True  # ✅ อนุมัติทันที
            )
            messages.success(request, f'สร้างชั้นเรียน "{subject_name}" สำเร็จ')
            return redirect('classroom_created')  # ✅ กลับมาหน้าเดิม

    return render(request, 'classroom_created.html', {
        'classrooms': classrooms  # ✅ ส่งข้อมูลไปให้ template
    })




@login_required
def join_classroom(request):
    if request.user.user_type != 'student':
        messages.error(request, 'เฉพาะนักเรียนเท่านั้นที่สามารถเข้าร่วมชั้นเรียนได้')
        return redirect('class_join_create')
    
    # ดึงคลาสที่เคยเข้าร่วม
    classrooms = request.user.enrolled_classes.filter(is_approved=True)

    if request.method == 'POST':
        form = JoinClassroomForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['classroom_code']
            try:
                classroom = Classroom.objects.get(code=code, is_approved=True)
                if request.user not in classroom.students.all():
                    classroom.students.add(request.user)
                    messages.success(request, f'เข้าร่วมชั้นเรียน {classroom.name} สำเร็จ')
                    return redirect('courses_enroll')
                else:
                    messages.info(request, 'คุณเป็นสมาชิกของชั้นเรียนนี้อยู่แล้ว')
                    return redirect('courses_enroll')  # กลับมาหน้าเดิม
            except Classroom.DoesNotExist:
                messages.error(request, 'ไม่พบชั้นเรียนที่มีรหัสนี้')
    else:
        form = JoinClassroomForm()
    
    return render(request, 'courses_enroll.html', {
        'form': form,
        'classrooms': classrooms  # ✅ ส่งข้อมูลคลาสเข้าร่วมไปยัง template
    })


@login_required
def classroom_home(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    
    # Check permissions
    if request.user != classroom.teacher and request.user not in classroom.students.all():
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงชั้นเรียนนี้')
        return redirect('class_join_create')
    
    return render(request, 'classroom_home.html', {'classroom': classroom})

@login_required
def logout_view(request):
    logger.info(f'User {request.user.email} logged out')
    logout(request)
    messages.success(request, 'ออกจากระบบแล้ว')
    return redirect('auth_view')


def upload_lesson_file(request):
    if request.method == 'POST' and request.FILES.get('lesson_file'):
        uploaded_file = request.FILES['lesson_file']
        if uploaded_file.size > 10 * 1024 * 1024:  # > 10MB
            return render(request, 'create_upload_image.html', {'error': 'File size must be under 10MB.'})
        if not uploaded_file.name.lower().endswith(('.pdf')):
            return render(request, 'create_upload_image.html', {'error': 'Invalid file format.'})
        fs = FileSystemStorage()
        fs.save(uploaded_file.name, uploaded_file)
        return redirect('success_page')
    return render(request, 'create_upload_image.html')


def upload_lesson_file_video(request):
    if request.method == 'POST' and request.FILES.get('lesson_file'):
        uploaded_file = request.FILES['lesson_file']
        if uploaded_file.size > 10 * 1024 * 1024:  # > 10MB
            return render(request, 'create_upload_video.html', {'error': 'File size must be under 10MB.'})
        if not uploaded_file.name.lower().endswith(('.pdf')):
            return render(request, 'create_upload_video.html', {'error': 'Invalid file format.'})
        fs = FileSystemStorage()
        fs.save(uploaded_file.name, uploaded_file)
        return redirect('success_page')
    return render(request, 'create_upload_video.html')

def notifications_view(request):
    notifications = [
        {
            'title': 'Update: Teacher Added A New Lesson In Science!',
            'description': 'Exciting lesson details! Don’t forget to pass the post-lesson quizzes.',
            'icon': 'fas fa-book-open',
            'bg_color': 'bg-green-500',
            'time': 'Just now'
        },
        {
            'title': 'Take the Test: You\'ve Completed The Science Test',
            'description': 'You did a great job. Keep the momentum going!',
            'icon': 'fas fa-vial',
            'bg_color': 'bg-purple-500',
            'time': 'Just now'
        },
        {
            'title': 'Download: Lesson Download Complete',
            'description': 'Science lesson download complete.',
            'icon': 'fas fa-download',
            'bg_color': 'bg-orange-400',
            'time': '7 hours ago'
        },
        {
            'title': 'System Notification: Security Check Scheduled',
            'description': 'Security check planned for Thursday at 2:00 PM.',
            'icon': 'fas fa-shield-alt',
            'bg_color': 'bg-red-300',
            'time': 'Yesterday'
        },
        # เพิ่มอีกตามต้องการ
    ]
    return render(request, 'notifications.html', {'notifications': notifications})

# urls.py (main project)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('classroom.urls')),
]


