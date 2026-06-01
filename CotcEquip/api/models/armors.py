from django.db import models

class Armor(models.Model):
    ARMOR_GROUPS = [
        ('Headgear',   'Headgear'),
        ('Body Armor', 'Body Armor'),
    ]

    name        = models.CharField(max_length=150, unique=True)
    armor_group = models.CharField(max_length=20, choices=ARMOR_GROUPS, default='Unknown')
    armor_type  = models.CharField(max_length=20, default='Other')
    p_def       = models.IntegerField(default=0)
    e_def       = models.IntegerField(default=0)
    p_atk       = models.IntegerField(default=0)
    e_atk       = models.IntegerField(default=0)
    spd         = models.IntegerField(default=0)
    crit        = models.IntegerField(default=0)
    hp          = models.IntegerField(default=0)
    sp          = models.IntegerField(default=0)
    extra       = models.TextField(default='')

    class Meta:
        db_table = 'armors'
        managed  = False

    def __str__(self):
        return f"{self.name} ({self.armor_group})"