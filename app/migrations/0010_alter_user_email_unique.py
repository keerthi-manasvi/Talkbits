# Step 3 of 3: now that no blank/duplicate emails remain, enforce uniqueness.
# NULL is not equal to NULL in SQL, so users with no email (NULL) never
# collide with each other -- only real duplicate addresses are blocked.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_normalize_blank_emails'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AddConstraint(
            model_name='userprogress',
            constraint=models.UniqueConstraint(fields=('user', 'course'), name='unique_progress_per_user_course'),
        ),
    ]
