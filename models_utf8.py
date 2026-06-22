# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Courses(models.Model):
    module = models.ForeignKey('Modules', models.DO_NOTHING)
    title = models.CharField(max_length=150)
    content = models.TextField()
    display_order = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'courses'
        unique_together = (('module', 'display_order'),)


class ExamEnrollments(models.Model):
    pk = models.CompositePrimaryKey('student_id', 'exam_id')
    student = models.ForeignKey('Students', models.DO_NOTHING)
    exam = models.ForeignKey('Exams', models.DO_NOTHING)
    enrolled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exam_enrollments'


class Exams(models.Model):
    module = models.ForeignKey('Modules', models.DO_NOTHING)
    exam_type = models.TextField()  # This field type is a guess.
    difficulty = models.TextField(blank=True, null=True)  # This field type is a guess.
    title = models.CharField(max_length=150)
    requirement_text = models.TextField()
    max_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    starting_topology = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exams'


class Laboratories(models.Model):
    module = models.ForeignKey('Modules', models.DO_NOTHING)
    title = models.CharField(max_length=150)
    instructions = models.TextField(blank=True, null=True)
    starting_topology = models.JSONField()

    class Meta:
        managed = False
        db_table = 'laboratories'


class ModuleEnrollments(models.Model):
    pk = models.CompositePrimaryKey('student_id', 'module_id')
    student = models.ForeignKey('Students', models.DO_NOTHING)
    module = models.ForeignKey('Modules', models.DO_NOTHING)
    enrolled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'module_enrollments'


class ModuleProfessors(models.Model):
    pk = models.CompositePrimaryKey('module_id', 'professor_id')
    module = models.ForeignKey('Modules', models.DO_NOTHING)
    professor = models.ForeignKey('Professors', models.DO_NOTHING)
    is_coordinator = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'module_professors'


class Modules(models.Model):
    title = models.CharField(unique=True, max_length=150)
    description = models.TextField(blank=True, null=True)
    image_url = models.CharField(max_length=255, blank=True, null=True)
    credits = models.IntegerField()
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'modules'


class Professors(models.Model):
    user = models.OneToOneField('Users', models.DO_NOTHING, primary_key=True)
    academic_title = models.TextField()  # This field type is a guess.
    department = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'professors'


class Students(models.Model):
    user = models.OneToOneField('Users', models.DO_NOTHING, primary_key=True)
    enrollment_year = models.IntegerField()
    study_group = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'students'


class Submissions(models.Model):
    student = models.ForeignKey(Students, models.DO_NOTHING)
    exam = models.ForeignKey(Exams, models.DO_NOTHING)
    evaluator = models.ForeignKey(Professors, models.DO_NOTHING, blank=True, null=True)
    answers_json = models.JSONField(blank=True, null=True)
    submitted_topology = models.JSONField(blank=True, null=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    ai_feedback = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)  # This field type is a guess.
    submitted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'submissions'


class Users(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(unique=True, max_length=100)
    password_hash = models.CharField(max_length=255)
    account_type = models.TextField()  # This field type is a guess.
    university = models.CharField(max_length=100, blank=True, null=True)
    faculty = models.CharField(max_length=100, blank=True, null=True)
    profile_picture_url = models.CharField(max_length=255, blank=True, null=True)
    status = models.TextField(blank=True, null=True)  # This field type is a guess.
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
