from django.urls import path
from . import views
from . import admin_views

app_name = 'lms'

urlpatterns = [
    # Student
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/results/', views.my_results, name='my_results'),
    path('enroll/<int:module_id>/', views.enroll_module, name='enroll_module'),
    path('enroll/code/', views.enroll_by_code, name='enroll_by_code'),
    path('module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('exam/<int:exam_id>/enroll/', views.enroll_exam, name='enroll_exam'),
    path('exam/<int:exam_id>/take/', views.take_exam, name='take_exam'),
    path('student/settings/general/', views.student_settings_general, name='student_settings_general'),
    # Professor
    path('professor/', views.professor_dashboard, name='professor_dashboard'),
    path('grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
    path('professor/settings/general/', views.professor_settings_general, name='professor_settings_general'),
    path('professor/settings/ai/', views.professor_ai_settings, name='professor_ai_settings'),
    
    # Admin Management
    path('manage/modules/', admin_views.manage_modules, name='admin_manage_modules'),
    path('manage/module/<int:module_id>/', admin_views.module_details, name='admin_module_details'),
    path('manage/module/<int:module_id>/add-course/', admin_views.add_course, name='admin_add_course'),
    path('manage/module/<int:module_id>/add-lab/', admin_views.add_lab, name='admin_add_lab'),
    path('manage/module/<int:module_id>/add-exam/', admin_views.add_exam, name='admin_add_exam'),
]
