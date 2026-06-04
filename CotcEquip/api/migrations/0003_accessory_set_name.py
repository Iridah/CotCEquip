# api/migrations/0003_accessory_set_name.py
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_accessory_armor_pet_weapon'),
    ]

    operations = [
        migrations.AddField(
            model_name='Accessory',
            name='set_name',
            field=models.CharField(max_length=100, null=True, blank=True, default=None),
        ),
    ]