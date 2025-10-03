from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    pass

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.CharField(max_length=255, blank=True, default="")  # Comma-separated course names (e.g., "Hindi,Tamil")
    xp = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"