# CotcEquip/api/models/accessories.py
from django.db import models

class Accessory(models.Model):
    name                = models.CharField(max_length=150, unique=True)
    is_a4               = models.BooleanField(default=False)
    p_atk               = models.IntegerField(default=0)
    e_atk               = models.IntegerField(default=0)
    p_def               = models.IntegerField(default=0)
    e_def               = models.IntegerField(default=0)
    spd                 = models.IntegerField(default=0)
    crit                = models.IntegerField(default=0)
    hp                  = models.IntegerField(default=0)
    sp                  = models.IntegerField(default=0)
    extra               = models.TextField(default='')
    set_name            = models.CharField(max_length=100, null=True, blank=True, default=None)
    is_exclusive        = models.BooleanField(default=False)
    exclusive_traveler  = models.CharField(max_length=150, null=True, blank=True, default=None)
    is_artifact         = models.BooleanField(default=False)
    imprint_req         = models.CharField(max_length=20, null=True, blank=True, default=None)
    source              = models.CharField(max_length=100, null=True, blank=True, default=None)

    class Meta:
        db_table = 'accessories'
        managed  = False

    def __str__(self):
        return self.name