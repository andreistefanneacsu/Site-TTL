from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # Modules
    path('module/create/', views.module_create, name='module_create'),
    path('module/<int:module_id>/edit/', views.module_edit, name='module_edit'),
    path('module/<int:module_id>/delete/', views.module_delete, name='module_delete'),
    path('module/<int:module_id>/assign-professor/', views.assign_professor, name='assign_professor'),
    path('module/<int:module_id>/remove-professor/<int:professor_id>/', views.remove_professor, name='remove_professor'),
    # Courses
    path('module/<int:module_id>/course/add/', views.course_create, name='course_create'),
    path('course/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('course/<int:course_id>/delete/', views.course_delete, name='course_delete'),
    # Labs
    path('module/<int:module_id>/lab/add/', views.lab_create, name='lab_create'),
    path('lab/<int:lab_id>/delete/', views.lab_delete, name='lab_delete'),
    # Exams
    path('module/<int:module_id>/exam/add/', views.exam_create, name='exam_create'),
    path('exam/<int:exam_id>/delete/', views.exam_delete, name='exam_delete'),
]
