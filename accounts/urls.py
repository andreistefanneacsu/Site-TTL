from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/add-professor/', views.create_professor, name='create_professor'),
    path('users/add-moderator/', views.create_moderator, name='create_moderator'),
    path('users/add-student/', views.add_student, name='add_student'),
]
