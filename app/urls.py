from django.urls import path, include
from . import views

urlpatterns = [ 
       
    path("", views.index, name="index"),
    path("signin", views.signin_view, name="signin"),
    path("logout", views.logout_view, name="logout"),
    path("SignUp", views.signup_view, name="signup"),
    path("register/<str:language>/", views.register_language, name="register"),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path("profile", views.profile, name="profile"),
    path("courses/", views.course_list, name="course_list"),
    path("unit/<str:language>/", views.unit_list, name="unit_list"),
    path("lessons/<str:language>/<int:unit>/", views.lesson_list, name="lesson_list"),
    path("lesson/<str:language>/<int:unit>/<int:lesson>/", views.lesson_detail, name="lesson_detail"),
    path("exercise/<str:language>/<int:unit>/<int:lesson>/", views.exercise_page, name="exercise_page"),
    path('registration-success/<str:language>/', views.registration_success, name='registration_success'),
    path("mycourses/", views.my_courses, name="my_courses"),


    ]

