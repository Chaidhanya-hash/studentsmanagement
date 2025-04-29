from django.urls import path
from .views import LoginView, AdminPanelView, AddUserView, AddCourseView, FacultyProfileView
from . import views 
from .views import AvailableCoursesView, EnrollCourseView, CourseDetailView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    # urls.py
    path('admin-panel/', AdminPanelView.as_view(), name='admin_panel'),
    path('add-user/', AddUserView.as_view(), name='add_user'),
    path('add-course/', AddCourseView.as_view(), name='add_course'),
    path('faculty-profile/', FacultyProfileView.as_view(), name='faculty_profile'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('available-courses/', AvailableCoursesView.as_view(), name='available_courses'),
    path('enroll/<int:course_id>/', EnrollCourseView.as_view(), name='enroll_course'),
    path('course/<int:course_id>/', CourseDetailView.as_view(), name='course_detail'),
    path('course/<int:course_id>/students/', views.student_details, name='student_details'),
    path('update-grade/', views.update_grade, name='update_grade'),

]
