# api/migrations/0004_accessory_exclusive_fields.py
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_accessory_set_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='Accessory',
            name='is_exclusive',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='Accessory',
            name='exclusive_traveler',
            field=models.CharField(max_length=150, null=True, blank=True, default=None),
        ),
    ]