from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Classroom
from django.utils import timezone

@admin.action(description='✅ อนุมัติผู้ใช้ที่เลือก')
def approve_selected_users(modeladmin, request, queryset):
    queryset.update(is_approved=True)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'user_type', 'is_approved', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_approved', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    actions = [approve_selected_users]
    ordering = ['-date_joined']

    fieldsets = UserAdmin.fieldsets + (
        ('ข้อมูลเพิ่มเติม', {
            'fields': ('user_type', 'is_approved', 'last_login_ip', 'failed_login_attempts'),
        }),
    )

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'teacher', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'code', 'teacher__email')
    readonly_fields = ('code', 'created_at')


# # ✅ Action และลงทะเบียน ClassroomRequest
# @admin.action(description='✅ อนุมัติคำขอสร้างห้องเรียน')
# def approve_selected_classroom_requests(modeladmin, request, queryset):
#     for classroom_request in queryset:
#         classroom_request.status = 'approved'
#         classroom_request.reviewed_by = request.user
#         classroom_request.reviewed_at = timezone.now()
#         classroom_request.save()

# @admin.register(ClassroomRequest)
# class ClassroomRequestAdmin(admin.ModelAdmin):
#     list_display = ('subject_name', 'teacher', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
#     list_filter = ('status', 'created_at')
#     search_fields = ('subject_name', 'teacher__email')
#     actions = [approve_selected_classroom_requests]
