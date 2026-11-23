from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('contact', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='contactsubmission',
            name='email_notification_pending',
            field=models.BooleanField(default=False),
        ),
    ]
