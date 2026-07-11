"""
Step 2 of 3: convert existing empty-string emails to NULL, and defensively
resolve any pre-existing case-insensitive duplicate emails, so the next
migration can safely add a unique constraint without breaking on old data.
"""
from django.db import migrations


def normalize_emails(apps, schema_editor):
    User = apps.get_model('app', 'User')

    User.objects.filter(email='').update(email=None)

    seen = {}
    for user in User.objects.exclude(email__isnull=True).exclude(email='').order_by('id'):
        key = user.email.strip().lower()
        if key in seen:
            user.email = f"{user.email}+dup{user.id}"
            user.save(update_fields=['email'])
        else:
            seen[key] = user.id


def reverse_noop(apps, schema_editor):
    # Not meaningfully reversible (can't tell which NULLs were originally '').
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_alter_user_email_nullable'),
    ]

    operations = [
        migrations.RunPython(normalize_emails, reverse_noop),
    ]
