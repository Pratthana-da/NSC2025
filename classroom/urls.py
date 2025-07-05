# urls.py (classroom app)
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.auth_view, name='home'),
    path('auth/', views.auth_view, name='auth_view'),
    path('class-create/', views.class_create_teacher, name='class_create'),
    path('class-join/', views.class_join_student, name='class_join'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('classroom-created/', views.create_classroom, name='classroom_created'),
    path('courses-enroll/', views.join_classroom, name='courses_enroll'),
    path('classroom/<uuid:classroom_id>/', views.classroom_home, name='classroom_home'),
    path('logout/', views.logout_view, name='logout'),
    path('courses-enrolled/', views.join_classroom, name='courses_enrolled'),
    path('api/classrooms/', views.classroom_list_api, name='api_classrooms'),
    path('accounts/auth/', views.auth_view, name='auth'),

    path('student/profile-settings-student/', views.profile_settings_student, name='profile_settings_student'),
    path('veiwe-profile-student/', views.view_profile_student, name='view_profile_student'),
    path('teacher/profile-settings-teacher/', views.profile_settings_teacher, name='profile_settings_teacher'),
    path('view-profile-teacher/', views.view_profile_teacher, name='view_profile_teacher'),

    path('classroom/<uuid:classroom_id>/create-upload/', views.upload_lesson_file, name='upload_lesson_file'),
    path('classroom/<uuid:classroom_id>/create-upload-video/', views.upload_lesson_file_video, name='upload_lesson_file_video'),
    path('notifications/', views.notifications_view, name='notifications'),



    path('storybook/<int:storybook_id>/view/', views.teacher_view_storybook, name='detail_lesson'),
    path('storybook/<int:storybook_id>/view-uploaded/', views.view_uploaded_lesson, name='view_uploaded_lesson'),

    path('student/storybook/<int:storybook_id>/view/', views.student_view_storybook, name='student_display_lesson'),
    path('select-role/', views.select_role_view, name='select_role'),



    path('final/<int:storybook_id>/', views.final, name='final'),

    path('storybook/<int:storybook_id>/cancel/', views.cancel_storybook, name='cancel_storybook'),


    path('storybook/<int:storybook_id>/status/', views.storybook_status, name='storybook_status'),
    path('api/storybook/<int:storybook_id>/status/', views.storybook_status_check_api, name='api_storybook_status'),
    # path('storybook/<int:storybook_id>/view/', views.view_storybook, name='view_storybook'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'),name='password_reset'),
    path('password_reset_done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_reset_done.html'),name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),name='password_reset_confirm'),
    path('password_reset_complete', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),name='password_reset_complete'),   
] 