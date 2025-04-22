from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decouple import config
from dotenv import load_dotenv
import os
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from .models import Course, Enrollment
from django.contrib.auth.decorators import login_required

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
                return render(request, 'accounts/admin_panel.html')
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
                return render(request, 'accounts/student_profile.html', {'user': request.user})
            else:
                messages.error(request, 'Invalid student credentials.')
                return redirect('login')

        else:
            messages.error(request, 'Invalid user type selected.')
            return redirect('login')

    # GET request
    return render(request, 'accounts/login.html')

# Define the admin panel view
def admin_panel(request):
    return render(request, 'accounts/admin_panel.html')


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


def student_profile(request):
    if request.user.is_staff:
        return redirect('faculty_profile')  # or handle unauthorized access
    return render(request, 'accounts/student_profile.html', {'user': request.user})

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