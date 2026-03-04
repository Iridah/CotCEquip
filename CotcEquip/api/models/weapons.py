from django.db import models

class Weapon(models.Model):
    WEAPON_TYPES = [
        ('Sword',   'Sword'),
        ('Dagger',  'Dagger'),
        ('Axe',     'Axe'),
        ('Bow',     'Bow'),
        ('Staff',   'Staff'),
        ('Polearm', 'Polearm'),
        ('Tome',    'Tome'),
        ('Fan',     'Fan'),
    ]

    name        = models.CharField(max_length=150, unique=True)
    weapon_type = models.CharField(max_length=20, choices=WEAPON_TYPES)
    series      = models.CharField(max_length=50, default='')
    level       = models.IntegerField(default=1)
    p_atk       = models.IntegerField(default=0)
    e_atk       = models.IntegerField(default=0)
    p_def       = models.IntegerField(default=0)
    e_def       = models.IntegerField(default=0)
    spd         = models.IntegerField(default=0)
    crit        = models.IntegerField(default=0)
    hp          = models.IntegerField(default=0)
    sp          = models.IntegerField(default=0)
    extra       = models.TextField(default='')
    slot_count  = models.IntegerField(default=0)
    soul_bonus_1 = models.CharField(max_length=20, null=True, blank=True)
    soul_bonus_2 = models.CharField(max_length=20, null=True, blank=True)
    soul_bonus_3 = models.CharField(max_length=20, null=True, blank=True)
    soul_bonus_4 = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'weapons'
        managed  = False

    def __str__(self):
        return f"{self.name} ({self.weapon_type} Lv.{self.level})"