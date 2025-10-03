from django.urls import path, include
from . import views

urlpatterns = [ 
       
    path("", views.index, name="index"),
    path("signin", views.signin_view, name="signin"),
    path("logout", views.logout_view, name="logout"),
    path("SignUp", views.signup_view, name="signup"),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path("profile", views.profile, name="profile")
    
    ]
"""
    
    path("register/<int:event_id>", views.register_view, name="register"),
    path("search", views.search, name="search"),
    """

