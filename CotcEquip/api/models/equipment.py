from django.db import models

class Weapon(models.Model):
    WEAPON_TYPES = [
        ('Sword', 'Sword'),
        ('Spear', 'Spear'),
        ('Dagger', 'Dagger'),
        ('Axe', 'Axe'),
        ('Bow', 'Bow'),
        ('Staff', 'Staff'),
        ('Tome', 'Tome'),
        ('Fan', 'Fan'),
    ]

    name = models.CharField(max_length=100)
    weapon_type = models.CharField(max_length=20, choices=WEAPON_TYPES)
    phys_atk = models.IntegerField(default=0)
    mag_atk = models.IntegerField(default=0)
    level_requirement = models.IntegerField(default=1)
    
    # Para armas que dan efectos especiales (ej: "Potency up")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.weapon_type})"

    class Meta:
        verbose_name = "Weapon"
        verbose_name_plural = "Weapons"