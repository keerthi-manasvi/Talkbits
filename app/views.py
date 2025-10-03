from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
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
import json
import os

def index(request):
    return render(request, 'app/index.html')

def signin_view(request):
    if request.user.is_authenticated:
        return redirect('index')  # Redirect authenticated users to homepage

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
        return redirect('index')  # Redirect authenticated users to homepage

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

        # Check if username (email/phone) already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email or phone number is already registered.')
            return render(request, 'app/signup.html')

        # Create inactive user
        try:
            user = User.objects.create_user(
                username=username,
                email=email if '@' in email else '',  # Set email if username is an email
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
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email or email],
                fail_silently=False,
            )

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
        login(request, user)
        messages.success(request, 'Email verified successfully! Start learning now.')
        return redirect('index')
    else:
        messages.error(request, 'Invalid verification link or it has expired.')
        return render(request, 'app/signin.html')

@login_required
def profile(request):
    return render(request, 'app/profile.html')

def logout_view(request):
    logout(request)  # Log out the user
    return render(request, 'app/logout.html')

def load_json(language: str) -> dict:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filename = f"{language.lower()}_translated.json"
    path = os.path.join(base_dir, 'lessons', filename)
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"lessons": []}

@login_required
def course_list(request):
    languages = ['Telugu', 'Hindi', 'English', 'Tamil']
    return render(request, 'app/index.html', {'languages': languages})

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
            }
        })
    lesson_data = lessons[lesson - 1]
    return render(request, 'app/lesson_detail.html', {
        'language': language,
        'unit': unit,
        'lesson': lesson,
        'lesson_data': lesson_data
    })

@login_required
def exercise_page(request, language, unit, lesson):
    data = load_json(language)
    lesson_data = data.get('lessons', [])[lesson - 1]
    exercises = [c for c in lesson_data.get('content', []) if c.get('type') == 'exercise']
    submitted = request.method == 'POST'
    if submitted:
        course_obj = Course.objects.filter(language=language).first()
        if course_obj:
            progress, _ = UserProgress.objects.get_or_create(user=request.user, course=course_obj)
            progress.exercises_submitted[str(lesson)] = True
            progress.save()
        return redirect('lesson_list', language=language, unit=unit)
    return render(request, 'app/exercise_page.html', {
        'language': language,
        'unit': unit,
        'lesson': lesson,
        'exercises': exercises
    })