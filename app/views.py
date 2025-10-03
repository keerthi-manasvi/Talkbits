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
