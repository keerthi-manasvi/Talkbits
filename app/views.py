from django.shortcuts import redirect, render,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail
from .models import Event, User, Feedback
import datetime
"""
# Create your views here.

def index(request):
    today = timezone.now().date()
    events = Event.objects.filter(date__gte=today).order_by('date')[:6]
    return render(request, 'app/index.html', {'events': events})

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "app/login.html", {
                "message": "Invalid username and/or password."
            })
    return render(request, "app/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

DROP1_DICT = {
    'option1': 'Student',
    'option2': 'Organizer',
}

def SignUp_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        selected_value = request.POST.get('drop1')

        selected_label = DROP1_DICT.get(selected_value, "Unknown")
        print(selected_value)
        print(selected_label)

        if password != confirmation:
            return render(request, "app/SignUp.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            if selected_value == "2":
                user.isOrganizer= True
            else:
                user.isOrganizer = False
            user.save()
        except IntegrityError:
            return render(request, "app/SignUp.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    return render(request, "app/SignUp.html")

def eventDetails_view(request, event_id):
    event = get_object_or_404(Event,id=event_id)
    return render(request, "app/eventDetails.html", {"event": event,"event_id": event_id})

def register_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        # Compose email to organizer
        subject = f"New Registration for {event.title}"
        message = f
        A new user has registered for your event:

        Name: {name}
        Email: {email}
        Phone: {phone}

        Event: {event.title}
        Date: {event.date.strftime('%d %B %Y')}
        
        organizer_email = event.organizer.email  

        send_mail(subject, message, 'noreply@app.com', [organizer_email])

        confirmation_subject = f"You're registered for {event.title}"
        confirmation_message = f
        Hi {name},

        Thank you for registering for {event.title} on {event.date.strftime('%d %B %Y')}.

        We look forward to seeing you there!

        — app Team
        
        send_mail(confirmation_subject, confirmation_message, 'noreply@app.com', [email])

        return redirect('eventDetails', event.id)

    return render(request, 'app/register.html', {'event': event})


def search(request):
    title = request.GET.get("title", "").strip().lower()
        
    if not title:
        return render(request, "app/error.html", {
            "message": "Please enter a search term."
        })
    
    matched_entries = Event.objects.filter(title__icontains= title)
    if matched_entries.exists():
        return render(request, "app/search.html", {
            "entries": matched_entries,
            "query": title
        })
    else:
        return render(request, "app/error.html", {
            "message": f"No events found matching '{title}'."
        })
"""