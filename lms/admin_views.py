from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from functools import wraps
from .models import Modules, Courses, Laboratories, Exams
import json

def login_required(roles=None):
    """Decorator that enforces login and optional role check."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if 'user_id' not in request.session:
                messages.error(request, 'Please log in first.')
                return redirect('accounts:login')
            if roles:
                role_list = roles if isinstance(roles, list) else [roles]
                if request.session.get('account_type') not in role_list:
                    messages.error(request, 'You do not have permission to access that page.')
                    return redirect('public:home')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

from django.utils import timezone

@login_required(roles=['ADMIN'])
def manage_modules(request):
    if request.method == 'POST':
        module_code = request.POST.get('module_code', '').strip()
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        credits_val = request.POST.get('credits', '5')
        
        try:
            Modules.objects.create(
                module_code=module_code,
                title=title,
                description=description,
                image_url='/static/images/basic.jpg',
                credits=int(credits_val),
                is_active=True,
                created_at=timezone.now()
            )
            messages.success(request, f'Module {module_code} created successfully!')
            return redirect('lms:admin_manage_modules')
        except Exception as e:
            messages.error(request, f'Failed to create module: {e}')
            
    modules = Modules.objects.all().order_by('id')
    return render(request, 'lms/admin/manage_modules.html', {'modules': modules})

@login_required(roles=['ADMIN'])
def module_details(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    courses = Courses.objects.filter(module=module).order_by('display_order')
    labs = Laboratories.objects.filter(module=module).order_by('id')
    exams = Exams.objects.filter(module=module).order_by('id')
    
    return render(request, 'lms/admin/module_details.html', {
        'module': module,
        'courses': courses,
        'labs': labs,
        'exams': exams
    })

@login_required(roles=['ADMIN'])
def add_course(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        display_order = request.POST.get('display_order', '1')
        
        try:
            Courses.objects.create(
                module=module,
                title=title,
                content=content,
                display_order=int(display_order)
            )
            messages.success(request, 'Course added successfully!')
            return redirect('lms:admin_module_details', module_id=module.id)
        except Exception as e:
            messages.error(request, f'Error adding course: {e}')
            
    return render(request, 'lms/admin/content_form.html', {
        'module': module,
        'content_type': 'Course'
    })

@login_required(roles=['ADMIN'])
def add_lab(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        instructions = request.POST.get('instructions', '').strip()
        topology_json = request.POST.get('topology', '').strip()
        
        try:
            parsed_topology = json.loads(topology_json) if topology_json else {}
            Laboratories.objects.create(
                module=module,
                title=title,
                instructions=instructions,
                starting_topology=parsed_topology,
                goal_topology={}
            )
            messages.success(request, 'Laboratory added successfully!')
            return redirect('lms:admin_module_details', module_id=module.id)
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format in Topology.')
        except Exception as e:
            messages.error(request, f'Error adding laboratory: {e}')
            
    return render(request, 'lms/admin/content_form.html', {
        'module': module,
        'content_type': 'Laboratory'
    })

@login_required(roles=['ADMIN'])
def add_exam(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        exam_type = request.POST.get('exam_type', 'THEORY')
        difficulty = request.POST.get('difficulty', 'INTERMEDIATE')
        requirement_text = request.POST.get('requirement_text', '').strip()
        max_score = request.POST.get('max_score', '10.00')
        passing_score = request.POST.get('passing_score', '5.00')
        topology_json = request.POST.get('topology', '').strip()
        
        try:
            parsed_topology = json.loads(topology_json) if topology_json else None
            Exams.objects.create(
                module=module,
                title=title,
                exam_type=exam_type,
                difficulty=difficulty,
                requirement_text=requirement_text,
                max_score=float(max_score),
                passing_score=float(passing_score),
                starting_topology=parsed_topology,
                goal_topology=None
            )
            messages.success(request, 'Exam added successfully!')
            return redirect('lms:admin_module_details', module_id=module.id)
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format in Topology/Questions.')
        except Exception as e:
            messages.error(request, f'Error adding exam: {e}')
            
    return render(request, 'lms/admin/content_form.html', {
        'module': module,
        'content_type': 'Exam'
    })
