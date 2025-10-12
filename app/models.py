from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom User model
class User(AbstractUser):
    pass

# Profile for tracking XP, streak, and enrolled courses
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.CharField(max_length=255, blank=True, default="")  # e.g., "Hindi,Tamil"
    xp = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Language choices
LANGUAGE_CHOICES = [
    ('Tamil', 'Tamil'),
    ('Hindi', 'Hindi'),
    ('Telugu', 'Telugu'),
    ('English', 'English'),  # Added English to match your app flow
]

# Course model
class Course(models.Model):
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    title = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.language} - {self.title}"

# Unit model
class Unit(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.course.language} - {self.title}"

# Lesson model
class Lesson(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.unit.title} - Lesson {self.order}: {self.title}"

# User progress tracking
class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    current_unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    current_lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    completed_lessons = models.ManyToManyField(Lesson, related_name='completed_by')
    exercises_submitted = models.JSONField(default=dict)
    exercise_scores = models.JSONField(default=dict) 
    
    def __str__(self):
        return f"{self.user.username} - {self.course.language}"

    def has_submitted_exercise(self, lesson_id):
        return str(lesson_id) in self.exercises_submitted and self.exercises_submitted[str(lesson_id)] is True

    def mark_exercise_submitted(self, lesson_id):
        self.exercises_submitted[str(lesson_id)] = True
        self.save()
        
    def save_exercise_score(self, lesson_id, prompt, score):
        if str(lesson_id) not in self.exercise_scores:
            self.exercise_scores[str(lesson_id)] = {}
        self.exercise_scores[str(lesson_id)][prompt] = score
        self.save()

class LanguageRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    learning_language = models.CharField(max_length=100)
    known_language = models.CharField(max_length=100)
    date_registered = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'learning_language')  # prevents duplicate registration

    def __str__(self):
        return f"{self.user.username} learns {self.learning_language} via {self.known_language}"

