from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# from django.db import models
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, is_staff=False):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, is_staff=is_staff)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        return self.create_user(email, name, password, is_staff=True)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email


class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})

    def __str__(self):
        return self.name

class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'is_staff': False})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.course.name}"

class Grade(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'is_staff': False})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks = models.FloatField()
    grade = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.student.name} - {self.course.name} - {self.grade}"
