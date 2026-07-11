import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Course, UserProgress, Profile
from app.exercise_engine import grade_exercise, grade_submission
from app.validators import StrongPasswordValidator, username_taken, email_taken
from django.core.exceptions import ValidationError

User = get_user_model()


class StrongPasswordValidatorTests(TestCase):
    def setUp(self):
        self.v = StrongPasswordValidator(min_length=6)

    def test_rejects_short_password(self):
        with self.assertRaises(ValidationError):
            self.v.validate("Ab1")

    def test_rejects_no_uppercase(self):
        with self.assertRaises(ValidationError):
            self.v.validate("abcdef1")

    def test_rejects_no_digit(self):
        with self.assertRaises(ValidationError):
            self.v.validate("Abcdefg")

    def test_accepts_valid_password(self):
        self.v.validate("Abcdef1")  # should not raise


class CaseInsensitiveUniquenessTests(TestCase):
    def test_username_case_insensitive_conflict(self):
        User.objects.create_user(username="Learner1", email="a@example.com", password="Abcdef1")
        self.assertTrue(username_taken("learner1"))
        self.assertTrue(username_taken("LEARNER1"))
        self.assertFalse(username_taken("learner2"))

    def test_email_case_insensitive_conflict(self):
        User.objects.create_user(username="u1", email="Someone@Example.com", password="Abcdef1")
        self.assertTrue(email_taken("someone@example.com"))
        self.assertFalse(email_taken("other@example.com"))

    def test_multiple_users_with_no_email_allowed(self):
        User.objects.create_user(username="u2", password="Abcdef1")
        User.objects.create_user(username="u3", password="Abcdef1")
        self.assertEqual(User.objects.filter(email__isnull=True).count(), 2)


class ExerciseGradingTests(TestCase):
    def test_fill_in_exact_match_case_insensitive(self):
        ex = {"format": "fill-in", "answer": "How"}
        self.assertTrue(grade_exercise(ex, "how")["correct"])
        self.assertFalse(grade_exercise(ex, "what")["correct"])

    def test_type_format_derives_answer_from_prompt(self):
        ex = {"format": "type", "prompt": "Type: I am a student."}
        self.assertTrue(grade_exercise(ex, "I am a student.")["correct"])
        self.assertFalse(grade_exercise(ex, "I am a teacher.")["correct"])

    def test_quiz_exact_match(self):
        ex = {"format": "quiz", "answer": "Good evening"}
        self.assertTrue(grade_exercise(ex, "Good evening")["correct"])

    def test_match_partial_scoring(self):
        ex = {
            "format": "match",
            "pairs": [
                {"word": "Hi", "match": "Hello"},
                {"word": "Bye", "match": "Goodbye"},
            ],
        }
        result = grade_exercise(ex, {"Hi": "Hello", "Bye": "wrong"})
        self.assertEqual(result["score"], 50.0)
        self.assertFalse(result["correct"])

    def test_grade_submission_aggregates_correctly(self):
        exercises = [
            {"format": "fill-in", "prompt": "p1", "answer": "cat"},
            {"format": "quiz", "question": "q1", "answer": "dog"},
        ]
        answers = [{"index": 0, "value": "cat"}, {"index": 1, "value": "wrong"}]
        result = grade_submission(exercises, answers)
        self.assertEqual(result["correct"], 1)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["score_percent"], 50.0)


class ExerciseSubmissionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="learner", email="learner@example.com", password="Abcdef1")
        self.client.force_login(self.user)

    def test_submit_exercises_grades_server_side_and_saves_progress(self):
        url = reverse('submit_exercises', args=['english', 1, 1])
        response = self.client.post(
            url,
            data=json.dumps({"answers": [{"index": 0, "value": "wrong-on-purpose"}]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('score_percent', data)
        self.assertIn('course_total_score', data)

        course = Course.objects.get(language__iexact='english')
        progress = UserProgress.objects.get(user=self.user, course=course)
        self.assertTrue(progress.has_submitted_exercise(1))

    def test_exercise_page_does_not_leak_answers(self):
        url = reverse('exercise_page', args=['english', 1, 1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # The correct answer for the first fill-in exercise in lesson 1 must
        # never appear in the rendered HTML.
        self.assertNotIn('"answer": "How"', content)
        self.assertNotIn("data-expected", content)
        self.assertNotIn("data-correct-option", content)


class ProfileAggregationTests(TestCase):
    def test_profile_shows_aggregated_course_scores(self):
        user = User.objects.create_user(username="scorer", email="scorer@example.com", password="Abcdef1")
        Profile.objects.get_or_create(user=user)
        course = Course.objects.create(language="Hindi", title="Hindi Course")
        progress = UserProgress.objects.create(user=user, course=course)
        progress.save_exercise_score(1, "prompt1", 80)
        progress.save_exercise_score(1, "prompt2", 100)

        self.client.force_login(user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "90.0%")  # average of 80 and 100
