import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GenTech.settings")
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# 1. Update Site Domain
site, created = Site.objects.get_or_create(id=1)
site.domain = "talkbits.onrender.com"
site.name = "Talkbits"
site.save()

# 2. Configure Google Social App from Environment Variables
client_id = os.environ.get("GOOGLE_CLIENT_ID")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

if client_id and client_secret:
    app, created = SocialApp.objects.get_or_create(
        provider="google",
        defaults={
            "name": "Google Auth",
            "client_id": client_id,
            "secret": client_secret,
        },
    )
    # Update credentials if they changed
    app.client_id = client_id
    app.secret = client_secret
    app.save()

    # Link site to the social application
    if site not in app.sites.all():
        app.sites.add(site)

    print("Successfully configured Google SocialApp and Site.")
else:
    print("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set. Skipping SocialApp setup.")