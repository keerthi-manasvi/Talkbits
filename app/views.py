from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
User=get_user_model()
from .models import *
from django.contrib import messages
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .forms import LanguageRegistrationForm
from .validators import username_taken, email_taken
from .exercise_engine import grade_submission
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import json
import os

def index(request):
    return render(request, 'app/index.html')

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import LanguageRegistration
from .forms import LanguageRegistrationForm  # assuming this exists

@login_required
def register_language(request, language):
    if LanguageRegistration.objects.filter(user=request.user, learning_language=language).exists():
        messages.error(request, f"You are already registered for {language}.")
        return redirect('course_list')
    if request.method == 'POST':
        form = LanguageRegistrationForm(request.POST, user=request.user)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.user = request.user
            registration.save()
            return redirect('registration_success', language=registration.learning_language)
    else:
        # Pre-fill the hidden field with the passed language
        form = LanguageRegistrationForm(initial={'learning_language': language}, user=request.user)

    registrations = LanguageRegistration.objects.filter(user=request.user)
    return render(request, 'app/register.html', {
        'form': form,
        'registrations': registrations,
        'language': language
    })

def my_courses(request):
    
    # Get all courses registered by the user
    registrations = LanguageRegistration.objects.filter(user=request.user)    
    return render(request, "app/my_courses.html", {"registrations": registrations})

@login_required
def registration_success(request, language):
    return render(request, 'app/registration_success.html', {'language': language})

def signin_view(request):
    if request.user.is_authenticated:
        return redirect('course_list')  # Redirect authenticated users to homepage

    if request.method == 'POST':
        username = request.POST.get('username')  # Supports email or phone
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)  # <-- Correct: log the user in
                return redirect('index')  # Redirect to homepage after successful login
            else:
                messages.error(request, 'Please verify your email address to log in.')
                return render(request, 'app/signin.html')
        else:
            messages.error(request, 'Invalid email/phone or password. Please try again.')
            return render(request, 'app/signin.html')

    return render(request, 'app/signin.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('course_list')  # Redirect authenticated users to homepage

    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')  # Email or phone
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validate inputs
        if not email or not username or not password or not confirm_password:
            messages.error(request, 'All required fields must be filled.')
            return render(request, 'app/signup.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'app/signup.html')

        try:
            validate_password(password)
        except ValidationError as e:
            for err in e.messages:
                messages.error(request, err)
            return render(request, 'app/signup.html')

        if username_taken(username):
            messages.error(request, 'This username is already taken.')
            return render(request, 'app/signup.html')

        if email_taken(email):
            messages.error(request, 'This email or phone number is already registered.')
            return render(request, 'app/signup.html')

        # Create inactive user
        try:
            user = User.objects.create_user(
                username=username,
                email=email if '@' in email else None,  # Set email if username is an email
                password=password,
                first_name=name.split()[0] if name else '',
                last_name=' '.join(name.split()[1:]) if name and len(name.split()) > 1 else '',
                is_active=False  # User cannot log in until email is verified
            )
            user.save()

            # Create profile for progress tracking
            Profile.objects.create(user=user)

            # Generate verification token and send email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = request.build_absolute_uri(
                reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
            )

            subject = 'Verify Your Email - APP'
            message = (
                f'Hi {user.first_name or user.username},\n\n'
                f'Welcome to APP! Please verify your email by clicking the link below:\n\n'
                f'{verification_url}\n\n'
                f'If you didn’t sign up, ignore this email.\n\n'
                f'Thanks,\nThe APP Team'
            )
            print("EMAIL_HOST_USER:", settings.EMAIL_HOST_USER)
            print("DEFAULT_FROM_EMAIL:", settings.DEFAULT_FROM_EMAIL)
            print("Recipient:", user.email or email)
            sent = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email or email],
                fail_silently=False,
            )
            print("Emails sent:", sent)

            messages.success(request, 'Account created! Please check your email to verify your account.')
            return render(request, 'app/signin.html')  # Redirect to signin with success message
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'app/signup.html')

    return render(request, 'app/signup.html')

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
        messages.success(request, 'Email verified successfully! Start learning now.')
        return redirect('index')
    else:
        messages.error(request, 'Invalid verification link or it has expired.')
        return render(request, 'app/signin.html')

@login_required
def profile(request):
    registrations = LanguageRegistration.objects.filter(user=request.user)
    progresses = UserProgress.objects.filter(user=request.user).select_related('course')

    course_scores = [
        {
            "language": p.course.language,
            "total_score": p.total_score,     # average % across all attempted exercises
            "total_points": p.total_points,    # sum of all exercise scores (XP-style total)
            "lessons_attempted": len(p.exercise_scores),
        }
        for p in progresses
    ]
    overall_average = (
        round(sum(c["total_score"] for c in course_scores) / len(course_scores), 1)
        if course_scores else 0
    )
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    return render(request, "app/profile.html", {
        "registrations": registrations,
        "course_scores": course_scores,
        "overall_average": overall_average,
        "profile_obj": profile_obj,
    })
def logout_view(request):
    logout(request)  # Log out the user
    return render(request, 'app/index.html')

def load_json(language: str) -> dict:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Updated path to point to app/languages/lessons/
    path = os.path.join(base_dir, 'languages', 'lessons', f"{language.lower()}.json")

    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Loaded {language}.json successfully with {len(data.get('lessons', []))} lessons")
            return data
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        return {"lessons": []}
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON decode error in {language}.json: {e}")
        return {"lessons": []}


def course_list(request):
    languages = ['Telugu', 'Hindi', 'English', 'Tamil']
    return render(request, 'app/course_list.html', {'languages': languages})

@login_required
def unit_list(request, language):
    return render(request, 'app/unit_list.html', {'language': language})

@login_required
def lesson_list(request, language, unit):
    data = load_json(language)
    lessons = data.get('lessons', [])
    return render(request, 'app/lesson_list.html', {
        'language': language,
        'unit': unit,
        'lessons': lessons
    })


@login_required
def lesson_detail(request, language, unit, lesson):
    data = load_json(language)
    lessons = data.get('lessons', [])

    if lesson - 1 >= len(lessons):
        return render(request, 'app/lesson_detail.html', {
            'language': language,
            'unit': unit,
            'lesson': lesson,
            'lesson_data': {
                'title': 'Lesson not found',
                'content': []
            },
            'target_lang': ''
        })

    lesson_data = lessons[lesson - 1]
    # Determine target language (user preference or dropdown)
    known= LanguageRegistration.objects.get(user=request.user, learning_language=language).known_language
    target_lang = request.GET.get('target_lang', known.lower())  # Default to known language

    # Load the translated file (e.g., telugu_translated_to_english.json)
    targ = f"{language.lower()}_translated_to_{target_lang}"
    translated_file = load_json(targ)
    trans_lessons = translated_file.get('lessons', [])

    # Make sure both lesson lists exist and have matching indices
    if lesson - 1 < len(trans_lessons):
        trans_lesson_data = trans_lessons[lesson - 1]
    else:
        trans_lesson_data = {"content": []}

    # Zip the original and translated content
    combined = list(zip(lesson_data.get('content', []), trans_lesson_data.get('content', [])))

    return render(request, 'app/lesson_detail.html', {
        'language': language,
        'unit': unit,
        'lesson': lesson,
        'lesson_data': lesson_data,   # for title etc.
        'combined': combined,         # zipped content
        'target_lang': target_lang
    })



# Fields that must NEVER reach the browser for a given exercise format --
# rendering these into the DOM (as the old template did via data-expected /
# data-correct-option attributes) lets anyone read the answer from view-source.
_SECRET_FIELDS_BY_FORMAT = {
    'fill-in': {'answer'},
    'quiz': {'answer'},
    'dialogue': {'answer'},
    'match': {'pairs'},  # the correct pairing itself; the "word" list is still needed by the client
}


def _public_exercise(exercise: dict, index: int) -> dict:
    """Return a client-safe copy of an exercise: no answer keys, plus its index."""
    safe = dict(exercise)
    for field in _SECRET_FIELDS_BY_FORMAT.get(exercise.get('format'), set()):
        safe.pop(field, None)
    if exercise.get('format') == 'match':
        # Client still needs the left-hand words and the shuffled right-hand
        # options to build the matching UI -- just not which word maps to
        # which option.
        pairs = exercise.get('pairs', [])
        safe['words'] = [p['word'] for p in pairs]
        safe['options'] = [p['match'] for p in pairs]
    safe['index'] = index
    return safe


@login_required
def exercise_page(request, language, unit, lesson):
    data = load_json(language)
    lesson_data = data.get('lessons', [])[lesson - 1]
    raw_exercises = [c for c in lesson_data.get('content', []) if c.get('type') == 'exercise']
    exercises = [_public_exercise(ex, i) for i, ex in enumerate(raw_exercises)]

    return render(request, 'app/exercise_page.html', {
        'language': language,
        'unit': unit,
        'lesson': lesson,
        'exercises': exercises,
        'exercises_json': json.dumps(exercises, ensure_ascii=False),
    })


@require_POST
@login_required
def submit_exercises(request, language, unit, lesson):
    """
    Grades an entire lesson's worth of exercise answers server-side and
    returns a score summary the frontend uses to render the popup modal.
    Expected JSON body: {"answers": [{"index": 0, "value": "How"}, ...]}
    """
    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    answers = body.get('answers', [])
    if not isinstance(answers, list):
        return JsonResponse({"error": "'answers' must be a list"}, status=400)

    data = load_json(language)
    lessons = data.get('lessons', [])
    if lesson - 1 >= len(lessons) or lesson - 1 < 0:
        return JsonResponse({"error": "Lesson not found"}, status=404)

    lesson_data = lessons[lesson - 1]
    exercises = [c for c in lesson_data.get('content', []) if c.get('type') == 'exercise']

    result = grade_submission(exercises, answers)

    course = Course.objects.filter(language__iexact=language).first()
    if course is None:
        # Auto-create the course row on first use; keeps DB in sync with the
        # static language content without needing a separate seed step.
        course = Course.objects.create(language=language.capitalize(), title=f"{language.capitalize()} Course")

    progress, _ = UserProgress.objects.get_or_create(user=request.user, course=course)
    for item in result['results']:
        progress.save_exercise_score(lesson_id=lesson, prompt=item['prompt'], score=item['score'])
    progress.mark_exercise_submitted(lesson)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.xp += int(result['score_percent'] / 10)
    profile.save(update_fields=['xp'])

    return JsonResponse({
        "score_percent": result['score_percent'],
        "correct": result['correct'],
        "total": result['total'],
        "results": result['results'],
        "course_total_score": progress.total_score,
        "xp": profile.xp,
    })

@csrf_exempt
@login_required
def save_exercise_score(request):
    """AJAX endpoint to save exercise score from the frontend."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    try:
        data = json.loads(request.body)
        language = data.get("language")
        lesson = data.get("lesson")
        prompt = data.get("prompt")
        score = data.get("score", 0)

        course = Course.objects.filter(language__iexact=language).first()
        if not course:
            return JsonResponse({"error": "Course not found"}, status=404)

        progress, _ = UserProgress.objects.get_or_create(user=request.user, course=course)
        progress.save_exercise_score(lesson, prompt, score)

        # Update XP (optional, tweak as needed)
        profile = Profile.objects.get(user=request.user)
        profile.xp += int(score / 10)  # e.g., 85% → +8 XP
        profile.save()

        return JsonResponse({"success": True, "xp": profile.xp})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
     
def service_worker(request):
    """
    Serve the service-worker.js from the static folder at the site root.
    """
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'service-worker.js')
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/javascript')
    except Exception as e:
        # Return an empty js file if not found to avoid 500 errors
        return HttpResponse('// service-worker not available', content_type='application/javascript')
