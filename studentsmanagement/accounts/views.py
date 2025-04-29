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
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic import DetailView
from django.http import HttpResponseForbidden
# Load environment variables
load_dotenv()

class LoginView(View):
    def get(self, request):
        return render(request, 'accounts/login.html')

    def post(self, request):
        user_type = request.POST.get('user_type')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if user_type == 'admin':
            return self.handle_admin_login(request, email, password)
        elif user_type == 'faculty':
            return self.handle_faculty_login(request, email, password)
        elif user_type == 'student':
            return self.handle_student_login(request, email, password)
        else:
            messages.error(request, 'Invalid user type selected.')
            return redirect('login')

    def handle_admin_login(self, request, email, password):
        admin_email = config('ADMIN_EMAIL')
        admin_password = config('ADMIN_PASSWORD')

        if email == admin_email and password == admin_password:
            faculty_users = User.objects.filter(is_staff=True)
            faculty_data = [
                {
                    'name': faculty.name,
                    'courses': [course.name for course in Course.objects.filter(faculty=faculty)]
                }
                for faculty in faculty_users
            ]
            return render(request, 'accounts/admin_panel.html', {'faculty_data': faculty_data})
        else:
            messages.error(request, 'Invalid admin credentials.')
            return redirect('login')

    def handle_faculty_login(self, request, email, password):
        user = authenticate(request, email=email, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            courses = Course.objects.filter(faculty=user)
            return render(request, 'accounts/faculty_profile.html', {'user': user, 'courses': courses})
        else:
            messages.error(request, 'Invalid faculty credentials.')
            return redirect('login')

    def handle_student_login(self, request, email, password):
        user = authenticate(request, email=email, password=password)
        if user is not None and not user.is_staff:
            login(request, user)
            student = request.user
            enrollments = Enrollment.objects.filter(student=student).select_related('course')
            grades = Grade.objects.filter(student=student)
            grade_dict = {grade.course.id: grade for grade in grades}

            enrolled_data = [
                {
                    'course_name': e.course.name,
                    'marks': grade_dict.get(e.course.id).marks if grade_dict.get(e.course.id) else 'N/A',
                    'grade': grade_dict.get(e.course.id).grade if grade_dict.get(e.course.id) else 'N/A',
                }
                for e in enrollments
            ]

            return render(request, 'accounts/student_profile.html', {
                'user': student,
                'enrolled_data': enrolled_data
            })
        else:
            messages.error(request, 'Invalid student credentials.')
            return redirect('login')


# Define the admin panel view

User = get_user_model()

class AdminPanelView(View):
    def get(self, request):
        faculty_users = User.objects.filter(is_staff=True).prefetch_related('course_set')
        
        faculty_data = [
            {
                'name': faculty.name,
                'courses': [course.name for course in Course.objects.filter(faculty=faculty)]
            }
            for faculty in faculty_users
        ]

        return render(request, 'accounts/admin_panel.html', {'faculty_data': faculty_data})




# Define the add_user view
User = get_user_model()

class AddUserView(View):
    def post(self, request):
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')  # 'student' or 'faculty'

        if user_type not in ['student', 'faculty']:
            messages.error(request, 'Invalid user type.')
            return redirect('admin_panel')
        if not name or not email or not password or not user_type:
            messages.error(request, "All fields are required.")
            return redirect('admin_panel')  # or wherever your admin panel is

        is_staff = user_type == 'faculty'

        if User.objects.filter(email=email).exists():
            messages.error(request, 'User with this email already exists.')
        else:
            User.objects.create_user(
                name=name,
                email=email,
                password=password,  # Django hashes it internally
                is_staff=is_staff
            )
            messages.success(request, f'{user_type.capitalize()} added successfully.')

        return redirect('admin_panel')

    def get(self, request):
        return redirect('admin_panel')



class AddCourseView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course_name = request.POST.get('course_name')
        if course_name:
            Course.objects.create(name=course_name, faculty=request.user)
        return redirect('faculty_profile')

    

class FacultyProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        faculty = request.user
        courses = Course.objects.filter(faculty=faculty)
        return render(request, 'accounts/faculty_profile.html', {
            'user': faculty,
            'courses': courses
        })


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



class AvailableCoursesView(ListView):
    model = Course
    template_name = 'accounts/available_courses.html'
    context_object_name = 'courses'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrolled_courses = Enrollment.objects.filter(student=self.request.user).values_list('course__id', flat=True)
        context['enrolled_course_ids'] = list(enrolled_courses)
        return context



class EnrollCourseView(View):
    def post(self, request, course_id):
        # Get the course
        course = get_object_or_404(Course, id=course_id)
        
        # Check if the student is already enrolled
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            Enrollment.objects.create(student=request.user, course=course)
        
        # Redirect to available courses page
        return redirect('available_courses')



class CourseDetailView(DetailView):
    model = Course
    template_name = 'accounts/student_details.html'
    context_object_name = 'course'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('course_id')
        return Course.objects.get(id=course_id)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        course = self.get_object()

        if user.is_authenticated and user.is_staff and course.faculty == user:
            # Faculty view their course
            enrolled_students = Enrollment.objects.filter(course=course)
            context['enrolled_students'] = enrolled_students
            return context
        else:
            return HttpResponseForbidden("You don't have permission to view this course.")




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



