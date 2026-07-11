# Step 1 of 3 for the email-uniqueness rollout: make the column nullable
# first (cheap, no data risk) before any data cleanup or constraint change.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_userprogress_exercise_scores_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
