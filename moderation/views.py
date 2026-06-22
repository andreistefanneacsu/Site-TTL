from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from functools import wraps
from lms.models import Modules, Courses, Laboratories, Exams, Users, Professors, ModuleProfessors


def mod_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.error(request, 'Please log in.')
            return redirect('accounts:login')
        if request.session.get('account_type') not in ('MODERATOR', 'ADMIN'):
            messages.error(request, 'Moderator access required.')
            return redirect('public:home')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ─── Dashboard ────────────────────────────────────────────────

@mod_required
def dashboard(request):
    modules = Modules.objects.all().order_by('-created_at')
    return render(request, 'moderation/dashboard.html', {'modules': modules})


# ─── Modules ──────────────────────────────────────────────────

@mod_required
def module_create(request):
    professors = Professors.objects.select_related('user').all()
    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        credits     = request.POST.get('credits', 0)
        image_url   = request.POST.get('image_url', '').strip()
        coord_id    = request.POST.get('coordinator_id')
        try:
            mod = Modules.objects.create(
                title=title, description=description,
                credits=int(credits), image_url=image_url or None,
                is_active=True
            )
            if coord_id:
                prof = get_object_or_404(Professors, user_id=int(coord_id))
                ModuleProfessors.objects.create(module=mod, professor=prof, is_coordinator=True)
            messages.success(request, f'Module "{title}" created.')
            return redirect('moderation:module_edit', module_id=mod.id)
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'moderation/module_form.html', {'professors': professors, 'action': 'Create'})


@mod_required
def module_edit(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    courses = Courses.objects.filter(module=module).order_by('display_order')
    labs    = Laboratories.objects.filter(module=module)
    exams   = Exams.objects.filter(module=module)
    professors = Professors.objects.select_related('user').all()
    assigned = [mp.professor_id for mp in ModuleProfessors.objects.filter(module=module)]

    if request.method == 'POST':
        module.title       = request.POST.get('title', module.title).strip()
        module.description = request.POST.get('description', module.description).strip()
        module.credits     = int(request.POST.get('credits', module.credits))
        module.image_url   = request.POST.get('image_url', '').strip() or None
        module.is_active   = request.POST.get('is_active') == 'on'
        module.save()
        messages.success(request, 'Module updated.')
        return redirect('moderation:module_edit', module_id=module.id)

    return render(request, 'moderation/module_edit.html', {
        'module': module, 'courses': courses, 'labs': labs, 'exams': exams,
        'professors': professors, 'assigned': assigned,
    })


@mod_required
def module_delete(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    if request.method == 'POST':
        title = module.title
        module.delete()
        messages.success(request, f'Module "{title}" deleted.')
        return redirect('moderation:dashboard')
    return render(request, 'moderation/confirm_delete.html', {'obj': module, 'type': 'Module'})


# ─── Courses ──────────────────────────────────────────────────

@mod_required
def course_create(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    if request.method == 'POST':
        title   = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        order   = request.POST.get('display_order', 1)
        try:
            Courses.objects.create(module=module, title=title, content=content, display_order=int(order))
            messages.success(request, f'Course "{title}" added.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('moderation:module_edit', module_id=module.id)
    return render(request, 'moderation/course_form.html', {'module': module, 'action': 'Add'})


@mod_required
def course_edit(request, course_id):
    course = get_object_or_404(Courses, id=course_id)
    if request.method == 'POST':
        course.title   = request.POST.get('title', course.title).strip()
        course.content = request.POST.get('content', course.content).strip()
        course.display_order = int(request.POST.get('display_order', course.display_order))
        course.save()
        messages.success(request, 'Course updated.')
        return redirect('moderation:module_edit', module_id=course.module_id)
    return render(request, 'moderation/course_form.html', {'course': course, 'module': course.module, 'action': 'Edit'})


@mod_required
def course_delete(request, course_id):
    course = get_object_or_404(Courses, id=course_id)
    module_id = course.module_id
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted.')
        return redirect('moderation:module_edit', module_id=module_id)
    return render(request, 'moderation/confirm_delete.html', {'obj': course, 'type': 'Course'})


# ─── Laboratories ─────────────────────────────────────────────

@mod_required
def lab_create(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    if request.method == 'POST':
        import json as _json
        title        = request.POST.get('title', '').strip()
        instructions = request.POST.get('instructions', '').strip()
        topology_raw = request.POST.get('starting_topology', '{}').strip()
        try:
            topology = _json.loads(topology_raw)
            Laboratories.objects.create(module=module, title=title, instructions=instructions, starting_topology=topology)
            messages.success(request, f'Lab "{title}" added.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('moderation:module_edit', module_id=module.id)
    return render(request, 'moderation/lab_form.html', {'module': module, 'action': 'Add'})


@mod_required
def lab_delete(request, lab_id):
    lab = get_object_or_404(Laboratories, id=lab_id)
    module_id = lab.module_id
    if request.method == 'POST':
        lab.delete()
        messages.success(request, 'Lab deleted.')
        return redirect('moderation:module_edit', module_id=module_id)
    return render(request, 'moderation/confirm_delete.html', {'obj': lab, 'type': 'Laboratory'})


# ─── Exams ────────────────────────────────────────────────────

@mod_required
def exam_create(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    if request.method == 'POST':
        import json as _json
        title            = request.POST.get('title', '').strip()
        exam_type        = request.POST.get('exam_type', 'THEORY')
        difficulty       = request.POST.get('difficulty', 'INTERMEDIATE')
        requirement_text = request.POST.get('requirement_text', '').strip()
        max_score        = request.POST.get('max_score', '10.00')
        passing_score    = request.POST.get('passing_score', '5.00')
        topology_raw     = request.POST.get('starting_topology', '').strip()
        topology = _json.loads(topology_raw) if topology_raw else None
        try:
            Exams.objects.create(
                module=module, title=title, exam_type=exam_type,
                difficulty=difficulty, requirement_text=requirement_text,
                max_score=float(max_score), passing_score=float(passing_score),
                starting_topology=topology
            )
            messages.success(request, f'Exam "{title}" created.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('moderation:module_edit', module_id=module.id)
    return render(request, 'moderation/exam_form.html', {'module': module, 'action': 'Add'})


@mod_required
def exam_delete(request, exam_id):
    exam = get_object_or_404(Exams, id=exam_id)
    module_id = exam.module_id
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted.')
        return redirect('moderation:module_edit', module_id=module_id)
    return render(request, 'moderation/confirm_delete.html', {'obj': exam, 'type': 'Exam'})


# ─── Assign Professor ─────────────────────────────────────────

@mod_required
def assign_professor(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    if request.method == 'POST':
        prof_id = request.POST.get('professor_id')
        is_coord = request.POST.get('is_coordinator') == 'on'
        try:
            prof = get_object_or_404(Professors, user_id=int(prof_id))
            obj, created = ModuleProfessors.objects.get_or_create(module=module, professor=prof)
            obj.is_coordinator = is_coord
            obj.save()
            messages.success(request, f'Professor assigned to {module.title}.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('moderation:module_edit', module_id=module.id)


@mod_required
def remove_professor(request, module_id, professor_id):
    mp = get_object_or_404(ModuleProfessors, module_id=module_id, professor_id=professor_id)
    if request.method == 'POST':
        mp.delete()
        messages.success(request, 'Professor removed from module.')
    return redirect('moderation:module_edit', module_id=module_id)
