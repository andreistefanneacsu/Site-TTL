from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    path('', views.home, name='home'),
    path('download/', views.download, name='download'),
    path('modules/', views.modules_list, name='modules'),
]
