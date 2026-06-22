from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from functools import wraps
from lms.models import Users, Students, Professors
import os


# ─── Permission helpers ────────────────────────────────────────────────────

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


# ─── Auth Views ────────────────────────────────────────────────────────────

def login_view(request):
    if request.session.get('user_id'):
        return _redirect_by_role(request.session.get('account_type'))

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, account_type FROM users "
                "WHERE email = %s AND password_hash = crypt(%s, password_hash)",
                [email, password]
            )
            row = cursor.fetchone()

        if row:
            user_id, account_type = row
            request.session['user_id'] = user_id
            request.session['account_type'] = account_type
            messages.success(request, 'Welcome back!')
            return _redirect_by_role(account_type)
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    request.session.flush()
    messages.info(request, 'You have been logged out.')
    return redirect('public:home')


def register_view(request):
    if request.method == 'POST':
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name', '').strip()
        email        = request.POST.get('email', '').strip()
        password     = request.POST.get('password', '')
        university   = request.POST.get('university', '').strip()
        faculty      = request.POST.get('faculty', '').strip()
        study_group  = request.POST.get('study_group', '').strip()
        enroll_year  = request.POST.get('enrollment_year', '2024')

        if not enroll_year:
            enroll_year = '2024'

        try:
            from django.db import transaction
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO users
                           (first_name, last_name, email, password_hash, account_type, university, faculty)
                           VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'STUDENT', %s, %s)
                           RETURNING id""",
                        [first_name, last_name, email, password, university, faculty]
                    )
                    user_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO students (user_id, enrollment_year, study_group) VALUES (%s, %s, %s)",
                        [user_id, int(enroll_year), study_group]
                    )
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('accounts:login')
        except Exception as e:
            messages.error(request, f'Registration failed: {e}')

    return render(request, 'accounts/register.html')


# ─── Profile ───────────────────────────────────────────────────────────────

@login_required()
def profile_view(request):
    user = Users.objects.get(id=request.session['user_id'])
    student = None
    professor = None
    try:
        student = Students.objects.get(user_id=user.id)
    except Students.DoesNotExist:
        pass
    try:
        professor = Professors.objects.get(user_id=user.id)
    except Professors.DoesNotExist:
        pass

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        university = request.POST.get('university', '').strip()
        faculty    = request.POST.get('faculty', '').strip()
        pic_url    = user.profile_picture_url or ''

        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            pic = request.FILES['profile_picture']
            upload_dir = os.path.join('media', 'profiles')
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"user_{user.id}_{pic.name}"
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'wb+') as dest:
                for chunk in pic.chunks():
                    dest.write(chunk)
            pic_url = f'/media/profiles/{filename}'

        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE users SET first_name=%s, last_name=%s,
                   university=%s, faculty=%s, profile_picture_url=%s
                   WHERE id=%s""",
                [first_name, last_name, university, faculty, pic_url, user.id]
            )
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'profile_user': user,
        'student': student,
        'professor': professor,
    })


# ─── Admin: Manage Users ───────────────────────────────────────────────────

@login_required(roles=['ADMIN', 'MODERATOR'])
def manage_users(request):
    """Admin & Moderator: list all users and manage roles."""
    account_type = request.session.get('account_type')
    users = Users.objects.all().order_by('account_type', 'last_name')
    return render(request, 'accounts/manage_users.html', {
        'users': users,
        'viewer_role': account_type,
    })


@login_required(roles=['ADMIN', 'MODERATOR'])
def create_professor(request):
    """Admin & Moderator: create a professor account."""
    if request.method == 'POST':
        first_name     = request.POST.get('first_name', '').strip()
        last_name      = request.POST.get('last_name', '').strip()
        email          = request.POST.get('email', '').strip()
        password       = request.POST.get('password', '')
        university     = request.POST.get('university', '').strip()
        faculty        = request.POST.get('faculty', '').strip()
        department     = request.POST.get('department', '').strip()
        academic_title = request.POST.get('academic_title', 'ASISTENT')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO users
                       (first_name, last_name, email, password_hash, account_type, university, faculty)
                       VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'PROFESSOR', %s, %s)
                       RETURNING id""",
                    [first_name, last_name, email, password, university, faculty]
                )
                user_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO professors (user_id, academic_title, department) VALUES (%s, %s, %s)",
                    [user_id, academic_title, department]
                )
            messages.success(request, f'Professor {first_name} {last_name} created.')
            return redirect('accounts:manage_users')
        except Exception as e:
            messages.error(request, f'Failed: {e}')

    return render(request, 'accounts/create_professor.html')


@login_required(roles=['ADMIN'])
def create_moderator(request):
    """Admin only: create a moderator account."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '')
        university = request.POST.get('university', '').strip()
        faculty    = request.POST.get('faculty', '').strip()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO users
                       (first_name, last_name, email, password_hash, account_type, university, faculty)
                       VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'MODERATOR', %s, %s)""",
                    [first_name, last_name, email, password, university, faculty]
                )
            messages.success(request, f'Moderator {first_name} {last_name} created.')
            return redirect('accounts:manage_users')
        except Exception as e:
            messages.error(request, f'Failed: {e}')

    return render(request, 'accounts/create_moderator.html')


@login_required(roles=['PROFESSOR'])
def add_student(request):
    """Professors can add students to the platform."""
    if request.method == 'POST':
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        email       = request.POST.get('email', '').strip()
        password    = request.POST.get('password', '')
        university  = request.POST.get('university', '').strip()
        faculty     = request.POST.get('faculty', '').strip()
        study_group = request.POST.get('study_group', '').strip()
        enroll_year = request.POST.get('enrollment_year', '2024')

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO users
                       (first_name, last_name, email, password_hash, account_type, university, faculty)
                       VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'STUDENT', %s, %s)
                       RETURNING id""",
                    [first_name, last_name, email, password, university, faculty]
                )
                user_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO students (user_id, enrollment_year, study_group) VALUES (%s, %s, %s)",
                    [user_id, int(enroll_year), study_group]
                )
            messages.success(request, f'Student {first_name} {last_name} added successfully.')
            return redirect('lms:professor_dashboard')
        except Exception as e:
            messages.error(request, f'Failed: {e}')

    return render(request, 'accounts/add_student.html')


# ─── Helpers ───────────────────────────────────────────────────────────────

def _redirect_by_role(account_type):
    if account_type == 'STUDENT':
        return redirect('lms:student_dashboard')
    elif account_type == 'PROFESSOR':
        return redirect('lms:professor_dashboard')
    elif account_type == 'MODERATOR':
        return redirect('moderation:dashboard')
    elif account_type == 'ADMIN':
        return redirect('accounts:manage_users')
    return redirect('public:home')
