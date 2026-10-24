from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from .validators import username_taken, email_taken


# Custom User model
class User(AbstractUser):
    # username already has unique=True (case-sensitive) from AbstractUser.
    # We additionally enforce case-insensitive uniqueness in clean(), since
    # SQLite has no native citext/ci-collation constraint worth adding for
    # a single field.
    # null=True (not just blank=True) matters here: SQL treats each NULL as
    # distinct, so multiple users with no email can coexist, while any two
    # users who DO share an email are still blocked by unique=True. Storing
    # '' for "no email" would collide instead, since '' unique-collides.
    email = models.EmailField(unique=True, blank=True, null=True)

    def clean(self):
        super().clean()
        if self.username and username_taken(self.username, exclude_pk=self.pk):
            raise ValidationError({'username': 'This username is already taken (case-insensitive match).'})
        if self.email and email_taken(self.email, exclude_pk=self.pk):
            raise ValidationError({'email': 'This email is already registered.'})

    def save(self, *args, **kwargs):
        # create_user() (and some callers) pass email='' rather than None
        # when no email is given. '' would collide with every other blank
        # email under the unique constraint, whereas NULL never collides
        # with NULL in SQL -- so normalize here regardless of call site.
        if self.email == '':
            self.email = None
        super().save(*args, **kwargs)


# Profile for tracking XP, streak, and enrolled courses
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.CharField(max_length=255, blank=True, default="")  # e.g., "Hindi,Tamil"
    xp = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Language choices
LANGUAGE_CHOICES = [
    ('Tamil', 'Tamil'),
    ('Hindi', 'Hindi'),
    ('Telugu', 'Telugu'),
    ('English', 'English'),  
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
    exercise_scores = models.JSONField(default=dict)  # {lesson_id: {prompt: score_0_to_100}}

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'course'], name='unique_progress_per_user_course')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.course.language}"

    def has_submitted_exercise(self, lesson_id):
        return str(lesson_id) in self.exercises_submitted and self.exercises_submitted[str(lesson_id)] is True

    def mark_exercise_submitted(self, lesson_id):
        self.exercises_submitted[str(lesson_id)] = True
        self.save(update_fields=['exercises_submitted'])

    def save_exercise_score(self, lesson_id, prompt, score):
        lesson_key = str(lesson_id)
        if lesson_key not in self.exercise_scores:
            self.exercise_scores[lesson_key] = {}
        self.exercise_scores[lesson_key][prompt] = score
        self.save(update_fields=['exercise_scores'])

    def lesson_score(self, lesson_id):
        """Average score (0-100) for a single lesson, or None if nothing submitted yet."""
        scores = self.exercise_scores.get(str(lesson_id), {})
        if not scores:
            return None
        return round(sum(scores.values()) / len(scores), 1)

    @property
    def total_score(self):
        """
        Aggregate score across every lesson attempted in this course.
        Computed on read from the JSON blob -- no denormalized column needed
        since exercise_scores per course is small (a few KB at most).
        """
        all_scores = []
        for lesson_scores in self.exercise_scores.values():
            all_scores.extend(lesson_scores.values())
        if not all_scores:
            return 0
        return round(sum(all_scores) / len(all_scores), 1)

    @property
    def total_points(self):
        """Sum (not average) of every exercise score -- used for XP-style totals."""
        total = 0
        for lesson_scores in self.exercise_scores.values():
            total += sum(lesson_scores.values())
        return round(total, 1)

class LanguageRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    learning_language = models.CharField(max_length=100)
    known_language = models.CharField(max_length=100)
    date_registered = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'learning_language')  # prevents duplicate registration

    def __str__(self):
        return f"{self.user.username} learns {self.learning_language} via {self.known_language}"

