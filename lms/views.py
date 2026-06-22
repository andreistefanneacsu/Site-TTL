from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.db import connection
from functools import wraps
from lms.models import (
    Users, Students, Professors, Modules, ModuleEnrollments,
    ModuleProfessors, Courses, Laboratories, Exams,
    ExamEnrollments, Submissions
)
import json


# ─── Permission Decorator ─────────────────────────────────────

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if 'user_id' not in request.session:
                messages.error(request, 'Please log in.')
                return redirect('accounts:login')
            if request.session.get('account_type') not in roles:
                messages.error(request, 'Access denied.')
                return redirect('public:home')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ─── Student Views ────────────────────────────────────────────

@role_required('STUDENT')
def student_dashboard(request):
    uid = request.session['user_id']
    student = get_object_or_404(Students, user_id=uid)
    enrolled = list(ModuleEnrollments.objects.filter(student=student).select_related('module'))
    enrolled_ids = [e.module_id for e in enrolled]
    available = Modules.objects.filter(is_active=True).exclude(id__in=enrolled_ids)

    # Recent submissions
    submissions = Submissions.objects.filter(student=student).order_by('-submitted_at')[:5]

    return render(request, 'lms/student_dashboard.html', {
        'student': student,
        'enrolled': enrolled,
        'available': available,
        'submissions': submissions,
    })


@role_required('STUDENT')
def enroll_module(request, module_id):
    uid = request.session['user_id']
    student = get_object_or_404(Students, user_id=uid)
    module  = get_object_or_404(Modules, id=module_id, is_active=True)

    if ModuleEnrollments.objects.filter(student=student, module=module).exists():
        messages.warning(request, 'You are already enrolled in this module.')
    else:
        ModuleEnrollments.objects.create(student=student, module=module)
        messages.success(request, f'Enrolled in "{module.title}" successfully!')

    return redirect('lms:student_dashboard')


@role_required('STUDENT')
def enroll_by_code(request):
    if request.method == 'POST':
        code = request.POST.get('module_code', '').strip().upper()
        uid = request.session['user_id']
        student = get_object_or_404(Students, user_id=uid)
        
        try:
            module = Modules.objects.get(module_code=code, is_active=True)
            if ModuleEnrollments.objects.filter(student=student, module=module).exists():
                messages.warning(request, f'You are already enrolled in {module.title}.')
            else:
                ModuleEnrollments.objects.create(student=student, module=module)
                messages.success(request, f'Successfully enrolled in "{module.title}"!')
        except Modules.DoesNotExist:
            messages.error(request, f'Module with code "{code}" not found or inactive.')
            
    return redirect('lms:student_dashboard')


@role_required('STUDENT')
def module_detail(request, module_id):
    module = get_object_or_404(Modules, id=module_id)
    uid = request.session['user_id']
    student = get_object_or_404(Students, user_id=uid)

    # Verify enrollment
    if not ModuleEnrollments.objects.filter(student=student, module=module).exists():
        messages.error(request, 'You are not enrolled in this module.')
        return redirect('lms:student_dashboard')

    courses = Courses.objects.filter(module=module).order_by('display_order')
    labs    = Laboratories.objects.filter(module=module)
    exams   = Exams.objects.filter(module=module)

    # Check existing enrollments and submissions for each exam
    exam_data = []
    for exam in exams:
        enrolled = ExamEnrollments.objects.filter(student=student, exam=exam).exists()
        submitted = Submissions.objects.filter(student=student, exam=exam).exists()
        exam_data.append({'exam': exam, 'enrolled': enrolled, 'submitted': submitted})

    return render(request, 'lms/module_detail.html', {
        'module': module,
        'courses': courses,
        'labs': labs,
        'exam_data': exam_data,
    })


@role_required('STUDENT')
def enroll_exam(request, exam_id):
    uid = request.session['user_id']
    student = get_object_or_404(Students, user_id=uid)
    exam = get_object_or_404(Exams, id=exam_id)

    if not ExamEnrollments.objects.filter(student=student, exam=exam).exists():
        ExamEnrollments.objects.create(student=student, exam=exam)
        messages.success(request, f'Enrolled for exam "{exam.title}".')

    return redirect('lms:module_detail', module_id=exam.module_id)


@role_required('STUDENT')
def take_exam(request, exam_id):
    uid = request.session['user_id']
    student = get_object_or_404(Students, user_id=uid)
    exam = get_object_or_404(Exams, id=exam_id)

    if Submissions.objects.filter(student=student, exam=exam).exists():
        messages.warning(request, 'You have already submitted this exam.')
        return redirect('lms:module_detail', module_id=exam.module_id)

    if request.method == 'POST':
        from django.utils import timezone
        
        # Check if it's a multiple choice exam
        is_mcq = exam.starting_topology and 'questions' in exam.starting_topology
        grade_val = None
        status_val = 'PENDING_REVIEW'
        answers_data = {}
        
        if is_mcq:
            questions = exam.starting_topology['questions']
            correct_count = 0
            for q in questions:
                q_id = str(q['id'])
                student_answer = request.POST.get(f'q_{q_id}')
                answers_data[q_id] = student_answer
                
                # Check if correct (student_answer is the string index of the option)
                if student_answer is not None and int(student_answer) == q['correct']:
                    correct_count += 1
            
            # Auto-grade
            score_per_question = float(exam.max_score) / len(questions)
            grade_val = correct_count * score_per_question
            status_val = 'GRADED'
            answers_data['type'] = 'multiple_choice'
        else:
            answers_text = request.POST.get('answers', '').strip()
            answers_data['text_answers'] = answers_text
            answers_data['type'] = 'text'

        Submissions.objects.create(
            student=student,
            exam=exam,
            answers_json=answers_data,
            grade=grade_val,
            status=status_val,
            submitted_at=timezone.now()
        )
        
        if is_mcq:
            messages.success(request, f'Exam submitted! Your auto-graded score is {grade_val:.2f}/{exam.max_score}.')
        else:
            messages.success(request, 'Exam submitted! Await grading from your professor.')
            
        return redirect('lms:student_dashboard')

    return render(request, 'lms/take_exam.html', {'exam': exam})



@role_required('STUDENT')
def my_results(request):
    uid = request.session['user_id']
    student = get_object_or_404(Students, user_id=uid)
    submissions = Submissions.objects.filter(student=student).order_by('-submitted_at')
    return render(request, 'lms/my_results.html', {'submissions': submissions})


@role_required('STUDENT')
def student_settings_general(request):
    uid = request.session['user_id']
    student = get_object_or_404(Students, user_id=uid)
    
    if request.method == 'POST':
        new_first_name = request.POST.get('first_name', '').strip()
        new_last_name = request.POST.get('last_name', '').strip()
        new_email = request.POST.get('email', '').strip()
        new_password = request.POST.get('password', '')
        
        try:
            with connection.cursor() as cursor:
                if new_password:
                    cursor.execute("UPDATE users SET first_name = %s, last_name = %s, email = %s, password_hash = crypt(%s, gen_salt('bf')) WHERE id = %s", 
                                   [new_first_name, new_last_name, new_email, new_password, uid])
                else:
                    cursor.execute("UPDATE users SET first_name = %s, last_name = %s, email = %s WHERE id = %s", 
                                   [new_first_name, new_last_name, new_email, uid])
            messages.success(request, 'Settings saved successfully.')
        except Exception as e:
            messages.error(request, f'Failed to update settings: {e}')
            
        return redirect('lms:student_settings_general')

    return render(request, 'lms/student_settings_general.html', {'student': student})


# ─── Professor Views ──────────────────────────────────────────

@role_required('PROFESSOR')
def professor_dashboard(request):
    uid = request.session['user_id']
    professor, _ = Professors.objects.get_or_create(
        user_id=uid,
        defaults={'academic_title': 'PROFESOR', 'department': 'General'}
    )
    prof_modules = [mp.module for mp in
                    ModuleProfessors.objects.filter(professor=professor).select_related('module')]
    module_ids = [m.id for m in prof_modules]

    pending = Submissions.objects.filter(
        exam__module_id__in=module_ids, status='PENDING_REVIEW'
    ).select_related('student__user', 'exam__module')

    graded = Submissions.objects.filter(
        exam__module_id__in=module_ids, status='GRADED'
    ).select_related('student__user', 'exam__module').order_by('-submitted_at')[:10]

    return render(request, 'lms/professor_dashboard.html', {
        'professor': professor,
        'modules': prof_modules,
        'pending': pending,
        'graded': graded,
    })


@role_required('PROFESSOR')
def professor_settings_general(request):
    uid = request.session['user_id']
    professor, _ = Professors.objects.get_or_create(
        user_id=uid,
        defaults={'academic_title': 'PROFESOR', 'department': 'General'}
    )
    
    if request.method == 'POST':
        new_first_name = request.POST.get('first_name', '').strip()
        new_last_name = request.POST.get('last_name', '').strip()
        new_email = request.POST.get('email', '').strip()
        new_password = request.POST.get('password', '')
        
        try:
            with connection.cursor() as cursor:
                if new_password:
                    cursor.execute("UPDATE users SET first_name = %s, last_name = %s, email = %s, password_hash = crypt(%s, gen_salt('bf')) WHERE id = %s", 
                                   [new_first_name, new_last_name, new_email, new_password, uid])
                else:
                    cursor.execute("UPDATE users SET first_name = %s, last_name = %s, email = %s WHERE id = %s", 
                                   [new_first_name, new_last_name, new_email, uid])
            messages.success(request, 'Settings saved successfully.')
        except Exception as e:
            messages.error(request, f'Failed to update settings: {e}')
            
        return redirect('lms:professor_settings_general')

    return render(request, 'lms/professor_settings_general.html', {'professor': professor})


@role_required('PROFESSOR')
def professor_ai_settings(request):
    uid = request.session['user_id']
    professor, _ = Professors.objects.get_or_create(
        user_id=uid,
        defaults={'academic_title': 'PROFESOR', 'department': 'General'}
    )

    return render(request, 'lms/professor_ai_settings.html', {
        'professor': professor,
        'providers': ['Google Gemini', 'OpenAI', 'Anthropic']
    })


@role_required('PROFESSOR')
def grade_submission(request, submission_id):
    uid = request.session['user_id']
    professor, _ = Professors.objects.get_or_create(
        user_id=uid,
        defaults={'academic_title': 'Profesor', 'department': 'General'}
    )
    submission = get_object_or_404(Submissions, id=submission_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'ai_grade':
            provider = request.POST.get('ai_provider')
            api_key = request.POST.get('ai_api_key')
            model_name = request.POST.get('ai_model')
            
            if not provider or not api_key:
                messages.error(request, 'Please configure your AI Provider and API Key in AI Settings first.')
                return redirect('lms:grade_submission', submission_id=submission.id)
                
            prompt = (
                f"You are a networking professor grading an exam.\n"
                f"Exam title: {submission.exam.title}\n"
                f"Requirement: {submission.exam.requirement_text}\n"
                f"Max score: {submission.exam.max_score}\n"
                f"Student text answers: {json.dumps(submission.answers_json)}\n"
                f"Respond ONLY with valid JSON: "
                f'{{ "suggested_grade": <number>, "feedback": "<string>" }}'
            )

            try:
                text = ""
                if provider == 'Google Gemini':
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_name or 'gemini-1.5-flash')
                    resp = model.generate_content(prompt)
                    text = resp.text.strip()
                elif provider == 'OpenAI':
                    import requests
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    data = {
                        "model": model_name or "gpt-4o",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2
                    }
                    r = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
                    if r.status_code == 200:
                        text = r.json()['choices'][0]['message']['content'].strip()
                    else:
                        raise Exception(f"OpenAI Error: {r.text}")
                elif provider == 'Anthropic':
                    import requests
                    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
                    data = {
                        "model": model_name or "claude-3-haiku-20240307",
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    r = requests.post("https://api.anthropic.com/v1/messages", json=data, headers=headers)
                    if r.status_code == 200:
                        text = r.json()['content'][0]['text'].strip()
                    else:
                        raise Exception(f"Anthropic Error: {r.text}")

                # Strip markdown fences if present
                if text.startswith('```'):
                    text = text.split('```')[1]
                    if text.startswith('json'):
                        text = text[4:]
                result = json.loads(text.strip())
                submission.grade = min(float(result['suggested_grade']), float(submission.exam.max_score))
                submission.ai_feedback = result.get('feedback', '')
                submission.save()
                messages.success(request, 'AI grading complete. Review the suggestion before publishing.')
            except Exception as e:
                messages.error(request, f'AI grading failed: {e}')

        elif action == 'publish':
            try:
                grade_val = float(request.POST.get('grade', 0))
                submission.grade = grade_val
                submission.evaluator = professor
                submission.status = 'GRADED'
                submission.save()
                messages.success(request, f'Grade {grade_val} published for {submission.student.user.first_name}.')
                return redirect('lms:professor_dashboard')
            except ValueError:
                messages.error(request, 'Invalid grade value.')

    return render(request, 'lms/grade_submission.html', {'submission': submission})
