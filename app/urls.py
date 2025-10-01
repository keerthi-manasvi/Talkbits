from django.urls import path
from . import views

urlpatterns = [
    """
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("SignUp", views.SignUp_view, name="SignUp"),
    path("register/<int:event_id>", views.register_view, name="register"),
    path("search", views.search, name="search"),
    """
]
