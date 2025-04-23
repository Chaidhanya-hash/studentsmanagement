from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decouple import config
from dotenv import load_dotenv
import os
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from .models import Course, Enrollment, Grade, User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from accounts.models import User


# Load environment variables
load_dotenv()

def login_view(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')  # 'admin', 'faculty', or 'student'
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Admin login
        if user_type == 'admin':
            admin_email = config('ADMIN_EMAIL')
            admin_password = config('ADMIN_PASSWORD')

            if email == admin_email and password == admin_password:
                faculty_users = User.objects.filter(is_staff=True)
                faculty_data = []
                for faculty in faculty_users:
                    courses = Course.objects.filter(faculty=faculty)
                    faculty_data.append({
                        'name': faculty.name,
                        'courses': [course.name for course in courses]
                    })

                return render(request, 'accounts/admin_panel.html', {'faculty_data': faculty_data})
            else:
                messages.error(request, 'Invalid admin credentials.')
                return redirect('login')

        # Faculty login
        elif user_type == 'faculty':
            user = authenticate(request, email=email, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                faculty = request.user
                courses = Course.objects.filter(faculty=faculty)
                return render(request, 'accounts/faculty_profile.html', {'user': faculty, 'courses': courses}) 
            else:
                messages.error(request, 'Invalid faculty credentials.')
                return redirect('login')

        # Student login
        elif user_type == 'student':
            user = authenticate(request, email=email, password=password)
            if user is not None and not user.is_staff:
                login(request, user)
                if request.user.is_staff:
                    return redirect('faculty_profile')  # or handle unauthorized access
                student = request.user

                # Get all enrollments of the student
                enrollments = Enrollment.objects.filter(student=student).select_related('course')

                # Get grades for the student
                grades = Grade.objects.filter(student=student)
                grade_dict = {grade.course.id: grade for grade in grades}

                enrolled_data = []
                for enrollment in enrollments:
                    course = enrollment.course
                    grade = grade_dict.get(course.id)
                    enrolled_data.append({
                        'course_name': course.name,
                        'marks': grade.marks if grade else 'N/A',
                        'grade': grade.grade if grade else 'N/A'
                    })

                return render(request, 'accounts/student_profile.html', {
                    'user': student,
                    'enrolled_data': enrolled_data
                })
            else:
                messages.error(request, 'Invalid student credentials.')
                return redirect('login')

        else:
            messages.error(request, 'Invalid user type selected.')
            return redirect('login')

    # GET request
    return render(request, 'accounts/login.html')

# Define the admin panel view

User = get_user_model()

def admin_panel(request):
    faculty_users = User.objects.filter(is_staff=True)
    
    faculty_data = []
    for faculty in faculty_users:
        courses = Course.objects.filter(faculty=faculty)
        faculty_data.append({
            'name': faculty.name,
            'courses': [course.name for course in courses]
        })

    return render(request, 'accounts/admin_panel.html', {'faculty_data': faculty_data})



# Define the add_user view
User = get_user_model()

def add_user(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')  # 'student' or 'faculty'

        if user_type == 'student':
            is_staff = False
        elif user_type == 'faculty':
            is_staff = True
        else:
            messages.error(request, 'Invalid user type.')
            return redirect('dashboard')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'User with this email already exists.')
        else:
            user = User.objects.create_user(
                name=name,
                email=email,
                password=password,  # this gets hashed internally
                is_staff=is_staff
            )
            messages.success(request, f'{user_type.capitalize()} added successfully.')

        return redirect('dashboard')  # change if needed

    return redirect('dashboard')


def add_course(request):
    if request.method == 'POST':
        course_name = request.POST.get('course_name')
        Course.objects.create(name=course_name, faculty=request.user)
        return redirect('faculty_profile')  # make sure this name matches your profile URL
    

def faculty_profile(request):
    faculty = request.user
    courses = Course.objects.filter(faculty=faculty)
    return render(request, 'accounts/faculty_profile.html', {'user': faculty, 'courses': courses}) 


from django.contrib.auth.decorators import login_required


@login_required
def student_profile(request):
    student = request.user

    # Get all enrollments of the student
    enrollments = Enrollment.objects.filter(student=student).select_related('course')

    # Get grades for the student
    grades = Grade.objects.filter(student=student)
    grade_dict = {grade.course.id: grade for grade in grades}

    enrolled_data = []
    for enrollment in enrollments:
        course = enrollment.course
        grade = grade_dict.get(course.id)
        enrolled_data.append({
            'course_name': course.name,
            'marks': grade.marks if grade else 'N/A',
            'grade': grade.grade if grade else 'N/A'
        })

    return render(request, 'accounts/student_profile.html', {
        'user': student,
        'enrolled_data': enrolled_data
    })


def available_courses(request):
    courses = Course.objects.all()
    enrolled_courses = Enrollment.objects.filter(student=request.user).values_list('course__id', flat=True)
    return render(request, 'accounts/available_courses.html', {
        'courses': courses,
        'enrolled_course_ids': list(enrolled_courses)
    })


def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Check if already enrolled
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        Enrollment.objects.create(student=request.user, course=course)
    return redirect('available_courses')


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    students = User.objects.filter(
        is_staff=False,
        enrollment__course=course
    ).distinct()
    grades = Grade.objects.filter(course=course)
    grade_dict = {grade.student.id: grade for grade in grades}

    return render(request, 'accounts/student_details.html', {
        'course': course,
        'students': students,
        'grades': grade_dict
    })



@login_required




@login_required
def student_details(request, course_id):
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    students = User.objects.filter(is_staff=False, enrollment__course=course).distinct()

    grades = Grade.objects.filter(course=course)
    grade_dict = {grade.student.id: grade for grade in grades}

    student_data = []
    for student in students:
        grade = grade_dict.get(student.id)
        student_data.append({
            'student': student,
            'marks': grade.marks if grade else '',
            'grade': grade.grade if grade else ''
        })

    return render(request, 'accounts/student_details.html', {
        'course': course,
        'student_data': student_data
    })





@require_POST




@login_required
def update_grade(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_id = request.POST.get('course_id')
        marks = request.POST.get('marks')
        grade = request.POST.get('grade')

        student = User.objects.get(id=student_id)
        course = Course.objects.get(id=course_id)

        # Create or update the grade
        grade_obj, created = Grade.objects.update_or_create(
            student=student,
            course=course,
            defaults={'marks': marks, 'grade': grade}
        )

        return redirect('student_details', course_id=course_id)



