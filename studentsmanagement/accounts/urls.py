from django.urls import path
from .views import login_view
from . import views 

urlpatterns = [
    path('login/', login_view, name='login'),
    # urls.py
    path('dashboard/', views.admin_panel, name='dashboard'),
    path('add_user/', views.add_user, name='add_user'),
    path('add-course/', views.add_course, name='add_course'),
    path('faculty/profile/', views.faculty_profile, name='faculty_profile'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/courses/', views.available_courses, name='available_courses'),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
]
