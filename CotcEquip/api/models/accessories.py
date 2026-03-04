from django.db import models

class Accessory(models.Model):
    name  = models.CharField(max_length=150, unique=True)
    is_a4 = models.BooleanField(default=False)
    p_atk = models.IntegerField(default=0)
    e_atk = models.IntegerField(default=0)
    p_def = models.IntegerField(default=0)
    e_def = models.IntegerField(default=0)
    spd   = models.IntegerField(default=0)
    crit  = models.IntegerField(default=0)
    hp    = models.IntegerField(default=0)
    sp    = models.IntegerField(default=0)
    extra = models.TextField(default='')

    class Meta:
        db_table = 'accessories'
        managed  = False

    def __str__(self):
        return self.name