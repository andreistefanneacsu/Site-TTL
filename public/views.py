from django.shortcuts import render
from lms.models import Modules

def home(request):
    return render(request, 'public/home.html')

def download(request):
    return render(request, 'public/download.html')

def modules_list(request):
    # Fetch active modules
    modules = Modules.objects.filter(is_active=True).order_by('id')
    return render(request, 'public/modules.html', {'modules': modules})
