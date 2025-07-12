# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.utils import timezone
from django.db.models import Q
from .models import TeacherID, User, Classroom
from .forms import SecureUserCreationForm, SecureAuthenticationForm, JoinClassroomForm
import logging
from django.http import HttpResponse 
from django.shortcuts import redirect, render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ClassroomSerializer
from django.contrib.auth.decorators import login_required
# views.py
# classroom/views.py


from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .forms import ProfileUpdateForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import LessonUploadForm
from .models import Lesson
# views.py
from django.shortcuts import render
# classroom/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Lesson
from .tasks import process_storybook_async
from .models import Lesson, Storybook, Scene
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib.auth import get_backends

from .models import Storybook
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
# from .models import TeacherRegistry
from .models import TeacherID
from django.contrib.auth.decorators import user_passes_test



from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Storybook, Report
from .forms import ReportForm

@csrf_exempt
@login_required
def submit_report(request, storybook_id):
    if request.method == "POST":
        storybook = get_object_or_404(Storybook, pk=storybook_id)
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.storybook = storybook
            report.save()
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "error", "errors": form.errors})
    return JsonResponse({"status": "invalid method"})




@login_required
def upload_lesson_file(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if request.method == 'POST':
        form = LessonUploadForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.user = request.user
            lesson.classroom = classroom  # 🔹 เชื่อมกับ classroom

            uploaded_file = request.FILES['file']
            filename = uploaded_file.name.rsplit('.', 1)[0]
            lesson.title = filename
            lesson.file = uploaded_file
            lesson.save()

            # ✅ สร้าง Storybook ที่เชื่อมกับ lesson
            storybook = Storybook.objects.create(
                user=request.user,
                classroom=classroom,  # 🔹 เพิ่ม relation ถ้ามี field นี้
                title=lesson.title,
                file=lesson.file
            )

            # ✅ เรียก Celery ทำงาน async
            process_storybook_async.delay(storybook.id)

            # ✅ redirect ไปหน้า status หรือ classroom_home ก็ได้
            return redirect('detail_lesson', storybook_id=storybook.id)

        else:
            print("❌ Form Errors:", form.errors)
    else:
        form = LessonUploadForm()

    return render(request, 'teacher/create_upload_image.html', {
        'form': form,
        'classroom': classroom
    })



# @login_required
# def storybook_status(request, storybook_id):
#     storybook = get_object_or_404(Storybook, id=storybook_id, user=request.user)
#     return render(request, 'teacher/storybook_status.html', {'storybook': storybook})


# @api_view(['GET'])
# def storybook_status_check_api(request, storybook_id):
#     storybook = get_object_or_404(Storybook, id=storybook_id)
#     total_created = Scene.objects.filter(storybook=storybook).count()
#     return Response({
#         'is_ready': storybook.is_ready,
#         'is_failed': storybook.is_failed,
#         'current_scene': total_created,
#         'total_scenes': 20
#     })




# @login_required
# def teacher_view_storybook(request, storybook_id):
#     storybook = get_object_or_404(Storybook, id=storybook_id, user=request.user)

#     scenes = storybook.scenes.order_by('scene_number')
#     context = {
#         'storybook': storybook,
#         'scenes': json.dumps(list(scenes.values('scene_number', 'text', 'image_url', 'audio_url')), cls=DjangoJSONEncoder)
#     }
#     return render(request, 'teacher/detail_lesson.html', context)

@login_required
def teacher_view_storybook(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id, user=request.user)

    context = {
        'storybook': storybook,
    }
    return render(request, 'teacher/detail_lesson.html', context)


@login_required
def view_uploaded_lesson(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id, user=request.user)
    posttest_questions = PostTestQuestion.objects.filter(storybook=storybook)

    scenes = storybook.scenes.order_by('scene_number')
    context = {
        'storybook': storybook,
        'questions': posttest_questions,
        'scenes': json.dumps(
            list(scenes.values('scene_number', 'text', 'image_url', 'audio_url')),
            cls=DjangoJSONEncoder
        ),
    }

    return render(request, 'teacher/view_uploaded_lesson.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from .models import Storybook, PostTestQuestion, PostTestSubmission, PostTestAnswer
from django.contrib.auth.decorators import login_required
import random

@login_required
def take_post_test(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id)
    questions = list(PostTestQuestion.objects.filter(storybook=storybook))

    if request.method == 'POST':
        total_correct = 0
        submission = PostTestSubmission.objects.create(
            user=request.user,
            storybook=storybook,
            score=0
        )

        for question in questions:
            selected = request.POST.get(f'question_{question.id}')
            if selected:
                selected = int(selected)
                PostTestAnswer.objects.create(
                    submission=submission,
                    question=question,
                    selected_choice=selected
                )
                if selected == question.correct_choice:
                    total_correct += 1

        submission.score = total_correct
        submission.save()
        return redirect('post_test_result', submission.id)

    # สุ่ม choices สำหรับแต่ละคำถาม
    randomized_questions = []
    for q in questions:
        choices = [
            (1, q.choice_1),
            (2, q.choice_2),
            (3, q.choice_3),
            (4, q.choice_4),
        ]
        random.shuffle(choices)
        randomized_questions.append({
            'question': q,
            'choices': choices
        })

    return render(request, 'student/post_test_form.html', {
        'storybook': storybook,
        'randomized_questions': randomized_questions,
    })

@login_required
def post_test_result(request, submission_id):
    submission = get_object_or_404(PostTestSubmission, id=submission_id, user=request.user)
    answers = submission.answers.all()

    return render(request, 'student/post_test_result.html', {
        'submission': submission,
        'answers': answers
    })


@login_required
def student_view_storybook(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id)

    # เช็คว่านักเรียนอยู่ใน classroom ของ storybook นี้ไหม
    if request.user not in storybook.classroom.students.all():
        return HttpResponseForbidden("You do not have permission to view this storybook.")

    context = {
        'storybook': storybook,
    }
    return render(request, 'student/detail_lesson_student.html', context)


def student_display_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'teacher/student_display_lesson.html', {'lesson': lesson})



def detail_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'teacher/detail_lesson.html', {'lesson': lesson})


def detail_lesson_all(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id)
    scenes = Scene.objects.filter(storybook=storybook)
    return render(request, 'student/detail_lesson_all.html', {
        'storybook': storybook,
        'scenes': scenes
    })





@login_required
def profile_settings_teacher(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile_settings_teacher')
    else:
        form = ProfileUpdateForm(instance=user)

    # ฟิลด์ที่ไม่ต้องแสดงใน Personal Info
    hidden_fields = [
        'profile_picture', 'bio', 'facebook', 'line',
        'teaching_subjects', 'class_code', 'classroom_link'
    ]

    return render(request, 'teacher/profile_settings_teacher.html', {
        'form': form,
        'hidden_fields': hidden_fields
    })


@login_required
def view_profile_teacher(request):
    form = ProfileUpdateForm(instance=request.user)
    hidden_fields = [
        'profile_picture', 'bio', 'facebook', 'line',
        'teaching_subjects', 'class_code', 'classroom_link'
    ]
    return render(request, 'teacher/view_profile_teacher.html', {
        'form': form,
        'user': request.user,
        'hidden_fields': hidden_fields,
    })

@login_required
def profile_settings_student(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile_settings_student')  # ✅ redirect กลับมา path ของ student
    else:
        form = ProfileUpdateForm(instance=user)

    hidden_fields = [
        'profile_picture', 'bio', 'facebook', 'line',
        'teaching_subjects', 'class_code', 'classroom_link'
    ]

    return render(request, 'student/profile_settings_student.html', {
        'form': form,
        'hidden_fields': hidden_fields
    })

@login_required
def view_profile_student(request):
    form = ProfileUpdateForm(instance=request.user)
    hidden_fields = [
        'profile_picture', 'bio', 'facebook', 'line',
        'teaching_subjects', 'class_code', 'classroom_link'
    ]
    return render(request, 'student/view_profile_student.html', {
        'form': form,
        'user': request.user,
        'hidden_fields': hidden_fields,
    })

@login_required
def profile_settings_admin(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile_settings_admin')  # ✅ redirect กลับมา path ของ student
    else:
        form = ProfileUpdateForm(instance=user)

    hidden_fields = [
        'profile_picture', 'bio', 'facebook', 'line',
        'teaching_subjects', 'class_code', 'classroom_link'
    ]

    return render(request, 'admin/profile_settings_admin.html', {
        'form': form,
        'hidden_fields': hidden_fields
    })

@login_required
def view_profile_admin(request):
    form = ProfileUpdateForm(instance=request.user)
    hidden_fields = [
        'profile_picture', 'bio', 'facebook', 'line',
        'teaching_subjects', 'class_code', 'classroom_link'
    ]
    return render(request, 'admin/view_profile_admin.html', {
        'form': form,
        'user': request.user,
        'hidden_fields': hidden_fields,
    })

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

@login_required
def select_role_view(request):
    user = request.user

    # ถ้ามี user_type แล้วไม่ต้องเลือกซ้ำ
    if user.user_type == 'teacher':
        return redirect('classroom_created')
    elif user.user_type == 'student':
        return redirect('courses_enroll')
    elif user.user_type == 'admin': 
        return redirect('admin_lesson_dashboard')

    if request.method == 'POST':
        role = request.POST.get('role')

        if role == 'teacher':
            input_code = request.POST.get('teacher_code')
            match = TeacherID.objects.filter(email=user.email, teacher_code=input_code).first()

            if match:
                user.user_type = 'teacher'
                user.is_approved = True
                user.save()
                return redirect('classroom_created')
            else:
                messages.error(request, "รหัสประจำตัวครูไม่ถูกต้อง หรือยังไม่ได้ลงทะเบียน")

        elif role == 'student':
            user.user_type = 'student'
            user.is_approved = True
            user.save()
            return redirect('courses_enroll')

    return render(request, 'select_a_role.html')

@csrf_protect
@never_cache
def auth_view(request):
    if request.user.is_authenticated:
        user = request.user
        if request.user.user_type == 'teacher':
            return redirect('classroom_created')
        elif request.user.user_type == 'student':
            return redirect('courses_enroll')
        elif request.user.user_type == 'admin':
            return redirect('admin_lesson_dashboard') 

    if request.method == 'POST':
        action = request.POST.get('action')
        print("🔍 action =", action)

        if action == 'login':
            form = SecureAuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                logger.info(f'User {user.email} logged in.')

                # ✅ Redirect based on user_type
                # if not user.user_type:
                #     return redirect('select_role')
                # elif user.user_type == 'teacher':
                #     return redirect('classroom_created')
                # elif user.user_type == 'student':
                #     return redirect('courses_enroll')
                # else:
                #     return redirect('select_role')

                if not user.user_type:
                    if user.is_superuser or user.is_staff:
                        user.user_type = 'admin'
                        user.save()
                        return redirect('admin_lesson_dashboard')
                else:
                    return redirect('select_role')

                # ✅ redirect ตาม user_type
                if user.user_type == 'teacher':
                    return redirect('classroom_created')
                elif user.user_type == 'student':
                    return redirect('courses_enroll')
                elif user.user_type == 'admin':
                    return redirect('admin_lesson_dashboard')

            else:
                logger.warning("❌ Failed login")
                messages.error(request, 'เข้าสู่ระบบไม่สำเร็จ')

        elif action == 'register':
            form = SecureUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_approved = True  # ✅ ไม่ต้องรออนุมัติ
                user.save()
                
                backend = get_backends()[0]
                user.backend = get_backends()[0].__module__ + "." + get_backends()[0].__class__.__name__

                login(request, user)
                logger.info(f'✅ New user registered: {user.email}')
                return redirect('select_role')
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
def class_create_teacher(request):
    if request.user.user_type == 'teacher':
        classrooms = Classroom.objects.filter(teacher=request.user)
    else:
        classrooms = Classroom.objects.none()

    return render(request, 'teacher/class_create.html', {
        'classrooms': classrooms
    })

@login_required
def class_join_student(request):
    if request.user.user_type == 'student':
        classrooms = request.user.enrolled_classes.all()
    else:
        classrooms = Classroom.objects.none()

    return render(request, 'student/class_join.html', {
        'classrooms': classrooms
    })



@login_required
@never_cache
def dashboard_view(request):
    if request.user.user_type == 'admin':
        return redirect('admin_dashboard')
    
    return render(request, 'teacher/class_join_create.html', {
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
        return redirect('classroom_created')

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

    return render(request, 'teacher/classroom_created.html', {
        'classrooms': classrooms  # ✅ ส่งข้อมูลไปให้ template
    })




@login_required
def join_classroom(request):
    if request.user.user_type != 'student':
        messages.error(request, 'เฉพาะนักเรียนเท่านั้นที่สามารถเข้าร่วมชั้นเรียนได้')
        return redirect('courses_enroll')
    
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
    
    return render(request, 'student/courses_enroll.html', {
        'form': form,
        'classrooms': classrooms  # ✅ ส่งข้อมูลคลาสเข้าร่วมไปยัง template
    })


@login_required
def classroom_home(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    # ตรวจสอบสิทธิ์เข้าถึง
    if request.user != classroom.teacher and request.user not in classroom.students.all():
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงชั้นเรียนนี้')
        return redirect('class_join_create')

    if request.user == classroom.teacher:
        # ✅ ครูเห็นเฉพาะ Storybook ที่ "ส่งงานแล้ว"
        storybooks = classroom.storybooks.filter(user=request.user, is_uploaded=True).order_by('-created_at')
        template_name = 'teacher/classroom_home.html'
    else:
        # นักเรียนเห็นเฉพาะที่ "พร้อมใช้งาน"
        storybooks = classroom.storybooks.filter(is_ready=True).order_by('-created_at')
        template_name = 'student/classroom_home.html'

    return render(request, template_name, {
        'classroom': classroom,
        'storybooks': storybooks
    })


import json
from django.contrib import messages
from .models import Storybook, PostTestQuestion

@login_required
def final(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id, user=request.user)

    if request.method == 'POST':
        # ✅ บันทึก download permission
        permission = request.POST.get('download_permission', 'public')
        storybook.download_permission = permission

        # ✅ อัปเดตชื่อเรื่องใหม่ (กรณีมีแก้ไข)
        title = request.POST.get('title')
        if title:
            storybook.title = title

        # ✅ ตั้งค่า is_uploaded
        storybook.is_uploaded = True
        storybook.save()

        # ✅ ดึงข้อมูลคำถามแบบทดสอบ
        questions_json = request.POST.get('questions_json')
        if questions_json:
            try:
                questions_data = json.loads(questions_json)

                for q in questions_data:
                    PostTestQuestion.objects.create(
                        storybook=storybook,
                        question_text=q['question'],
                        choice_1=q['choices'][0],
                        choice_2=q['choices'][1],
                        choice_3=q['choices'][2],
                        choice_4=q['choices'][3],
                        correct_choice=q['correct']
                    )
            except Exception as e:
                messages.error(request, f"เกิดข้อผิดพลาดในการบันทึกคำถาม: {str(e)}")

        messages.success(request, "อัปโหลดสำเร็จ!")
        return redirect('classroom_home', classroom_id=storybook.classroom.id)

    return redirect('detail_lesson', storybook_id=storybook.id)



# views.py
from django.contrib import messages
from django.views.decorators.http import require_POST

@login_required
@require_POST
def cancel_storybook(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id, user=request.user)

    classroom_id = storybook.classroom.id  # เก็บก่อนลบ
    storybook.delete()
    messages.warning(request, "ยกเลิกและลบนิทานเรียบร้อยแล้ว")

    return redirect('upload_lesson_file', classroom_id=classroom_id)



@login_required
def logout_view(request):
    logger.info(f'User {request.user.email} logged out')
    logout(request)
    messages.success(request, 'ออกจากระบบแล้ว')
    return redirect('auth_view')

def upload_lesson_file_video(request):
    if request.method == 'POST' and request.FILES.get('lesson_file'):
        uploaded_file = request.FILES['lesson_file']
        if uploaded_file.size > 10 * 1024 * 1024:  # > 10MB
            return render(request, 'teacher/create_upload_video.html', {'error': 'File size must be under 10MB.'})
        if not uploaded_file.name.lower().endswith(('.pdf')):
            return render(request, 'teacher/create_upload_video.html', {'error': 'Invalid file format.'})
        fs = FileSystemStorage()
        fs.save(uploaded_file.name, uploaded_file)
        return redirect('success_page')
    return render(request, 'teacher/create_upload_video.html')


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
    return render(request, 'teacher/notifications.html', {'notifications': notifications})

@login_required
def delete_storybook(request, storybook_id):
    if request.method == 'POST':
        storybook = get_object_or_404(Storybook, id=storybook_id)

        # ✅ ตรวจสอบสิทธิ์ (เฉพาะ admin หรือเจ้าของ)
        if request.user.user_type == 'admin' or request.user == storybook.user:
            storybook.delete()
            messages.success(request, "ลบบทเรียนเรียบร้อยแล้ว")
        else:
            messages.error(request, "คุณไม่มีสิทธิ์ลบบทเรียนนี้")

    return redirect('admin_lesson_dashboard')

# @login_required
# def admin_lesson_dashboard(request):
#     if request.user.user_type != 'admin':
#         return redirect('select_role')  # class_join_createป้องกันคนอื่นเข้า

#     total_users = User.objects.exclude(user_type='admin').count()
#     total_storybooks = Storybook.objects.count()
#     storybooks = Storybook.objects.select_related('classroom', 'user').order_by('-created_at')

#     context = {
#         'total_users': total_users,
#         'total_storybooks': total_storybooks,
#         'storybooks': storybooks
#     }
#     return render(request, 'admin/dashboard_lesson_admin.html', context)


@login_required
def user_list_view(request):
    teachers = User.objects.filter(user_type='teacher')
    students = User.objects.filter(user_type='student')

    teacher_ids = TeacherID.objects.all()
    teacher_id_map = {t.email: t.teacher_code for t in teacher_ids}

    context = {
        "teachers": teachers,
        "students": students,
        "teacher_id_map": teacher_id_map,  # ส่งไป template
    }
    return render(request, 'admin/user_list.html', context)


def add_teacher_registry_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        teacher_code = request.POST.get("teacher_id")

        if not TeacherID.objects.filter(email=email, teacher_code=teacher_code).exists():
            TeacherID.objects.create(
                full_name=full_name,
                email=email,
                teacher_code=teacher_code
            )
            messages.success(request, "เพิ่มข้อมูลสำเร็จ")
            return redirect("add_teacher_registry")  # หรือชื่อ path ที่คุณใช้
        else:
            messages.error(request, "มีครูคนนี้อยู่แล้ว")

    # ✅ ดึงรายชื่อครูทั้งหมดมาส่งไปให้ template
    registered_teachers = TeacherID.objects.all()

    return render(request, "admin/add_teacher_registry.html", {
        "registered_teachers": registered_teachers
    })


def delete_teacher_view(request, teacher_id):
    if request.method == 'POST':
        teacher = get_object_or_404(TeacherID, id=teacher_id)
        teacher.delete()
        messages.success(request, "ลบคุณครูเรียบร้อยแล้ว")
    return redirect('add_teacher_registry')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def delete_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('user_list')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def teacher_lesson_list_view(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, user_type='teacher')
    lessons = Lesson.objects.filter(user=teacher)  # ถ้ามี foreignkey เป็น user

    context = {
        "teacher": teacher,
        "lessons": lessons,
    }
    return render(request, 'admin/teacher_lessons.html', context)

# @login_required
# @user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
# def delete_teacher_lesson_view(request, lesson_id):
#     lesson = get_object_or_404(Lesson, id=lesson_id)
#     teacher_id = lesson.user.id
#     lesson.delete()
#     return redirect('teacher_lesson_list', teacher_id=teacher_id)
@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def delete_teacher_storybook_view(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id)
    teacher_id = storybook.user.id
    storybook.delete()
    return redirect('teacher_storybooks_admin', teacher_id=teacher_id)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def delete_teacher_lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    teacher_id = lesson.user.id
    lesson.delete()
    return redirect('teacher_storybooks_admin', teacher_id=teacher_id)
# @login_required
# @user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
# def admin_view_lesson_detail(request, lesson_id):
#     # lesson = get_object_or_404(Lesson, id=lesson_id)
#     storybook = Storybook.objects.filter(lesson=lesson).first()
#     scenes = storybook.scenes.order_by('scene_number')  
#     # scenes = storybook.scenes.all() if storybook else []

#     context = {
#         'storybook': storybook,
#         'scenes': scenes,
#     }
#     return render(request, 'admin/lesson_detail.html', context)
    # return render(request, 'admin/lesson_detail.html', {
    #     'lesson': lesson,
    #     'storybook': storybook,
    #     'scenes': scenes
    # })
@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def admin_view_lesson_detail(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id)
    scenes = storybook.scenes.order_by('scene_number')
    return render(request, 'admin/view_lesson_detail.html', {
        'storybook': storybook,
        'scenes': scenes,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def teacher_storybooks_admin_view(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id)
    storybooks = Storybook.objects.filter(user=teacher).order_by('-created_at')
    return render(request, 'admin/teacher_storybooks.html', {
        'teacher': teacher,
        'storybooks': storybooks,
    })

# @login_required
# @user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')  # หรือใช้ is_staff แล้วแต่สิทธิ์แอดมินของคุณ
# def admin_reported_lessons_view(request):
#     reports = Report.objects.select_related('storybook', 'user').order_by('-created_at')
#     return render(request, 'admin/dashboard_lesson_admin.html', {
#         'reports': reports,
#         'total_users': User.objects.count(),
#         'total_storybooks': Storybook.objects.count(),
#     })

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def admin_reported_lessons_view(request):
    reports = Report.objects.select_related('storybook', 'user').order_by('-created_at')
    total_users = User.objects.exclude(user_type='admin').count()
    total_storybooks = Storybook.objects.count()
    storybooks = Storybook.objects.select_related('classroom', 'user').order_by('-created_at')

    return render(request, 'admin/dashboard_lesson_admin.html', {
        'reports': reports,
        'total_users': total_users,
        'total_storybooks': total_storybooks,
        'storybooks': storybooks,
    })

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def admin_report_detail_view(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id)
    reports = Report.objects.filter(storybook=storybook).select_related('user')
    return render(request, 'admin/report_detail.html', {
        'storybook': storybook,
        'reports': reports,
    })

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def delete_reported_storybook(request, storybook_id):
    storybook = get_object_or_404(Storybook, id=storybook_id)
    storybook.delete()
    messages.success(request, "ลบบทเรียนเรียบร้อยแล้ว")
    return redirect('admin_reported_lessons')