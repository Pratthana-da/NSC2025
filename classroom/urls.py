# urls.py (classroom app)
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.auth_view, name='home'),
    path('auth/', views.auth_view, name='auth_view'),
    path('class-join-create/', views.dashboard, name='class_join_create'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('classroom-created/', views.create_classroom, name='classroom_created'),
    path('courses-enroll/', views.join_classroom, name='courses_enroll'),
    path('classroom/<uuid:classroom_id>/', views.classroom_home, name='classroom_home'),
    path('logout/', views.logout_view, name='logout'),
    path('courses-enrolled/', views.join_classroom, name='courses_enrolled'),
    path('api/classrooms/', views.classroom_list_api, name='api_classrooms'),
    path('accounts/auth/', views.auth_view, name='auth'),
    path('profile-settings/', views.profile_settings, name='profile_settings'),
    path('veiwe-profile/', views.veiwe_profile, name='veiwe_profile'),


    # path('choose-role/', views.choose_role_view, name='choose_role'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'),name='password_reset'),
    path('password_reset_done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_reset_done.html'),name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),name='password_reset_confirm'),
    path('password_reset_complete', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),name='password_reset_complete'),   
]