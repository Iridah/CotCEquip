from django.db import models

class Pet(models.Model):
    name         = models.CharField(max_length=100, unique=True)
    hp           = models.IntegerField(default=0)
    p_atk        = models.IntegerField(default=0)
    e_atk        = models.IntegerField(default=0)
    p_def        = models.IntegerField(default=0)
    e_def        = models.IntegerField(default=0)
    spd          = models.IntegerField(default=0)
    crit         = models.IntegerField(default=0)
    skill_name   = models.CharField(max_length=100, default='')
    skill_effect = models.TextField(default='')

    class Meta:
        db_table = 'pets'
        managed  = False

    def __str__(self):
        return self.name