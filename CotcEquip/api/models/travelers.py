from django.db import models


class Traveler(models.Model):
    """
    Catálogo de personajes. Datos estáticos del CSV.
    No se edita desde el frontend del usuario.
    """
    name = models.CharField(max_length=100, unique=True)
    rarity = models.IntegerField(default=5)
    job = models.CharField(max_length=50)
    weapon_type = models.CharField(max_length=50, default='Unknown')
    element = models.CharField(max_length=100)
    is_released = models.BooleanField(default=True)

    # Stats base a nivel 120
    hp_120 = models.IntegerField(default=0)
    sp_120 = models.IntegerField(default=0)
    p_atk_120 = models.IntegerField(default=0)
    p_def_120 = models.IntegerField(default=0)
    e_atk_120 = models.IntegerField(default=0)
    e_def_120 = models.IntegerField(default=0)
    crit_120 = models.IntegerField(default=0)
    spd_120 = models.IntegerField(default=0)

    # Evaluación de rol (calculada, no la toca el usuario)
    p_dps = models.CharField(max_length=5, default="C")
    e_dps = models.CharField(max_length=5, default="C")
    tankiness = models.CharField(max_length=5, default="C")
    healer = models.CharField(max_length=5, default="C")
    buffer = models.CharField(max_length=5, default="C")
    debuffer = models.CharField(max_length=5, default="C")
    breaker = models.CharField(max_length=5, default="C")
    damage_coverage = models.IntegerField(default=0)
    total_score = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'travelers_master'
        managed = False

    def __str__(self):
        return self.name


class RosterEntry(models.Model):
    """
    Estado del viajero en el roster del usuario.
    Esto es lo que se edita desde el frontend.
    """
    traveler = models.OneToOneField(
        Traveler,
        on_delete=models.CASCADE,
        related_name='roster_entry'
    )

    # Lo que cargás manualmente
    is_obtained = models.BooleanField(default=False)
    is_6_stars = models.BooleanField(default=False)
    current_level = models.IntegerField(default=1)
    awakening_level = models.IntegerField(default=0)
    ultimate_level = models.IntegerField(default=0)
    is_ultimate_awakened = models.BooleanField(default=False)
    has_ultimate_overcharge = models.BooleanField(default=False)

    # Blessing of the Lantern
    lantern_blessing_active = models.BooleanField(default=False)
    bless_hp = models.IntegerField(default=0)
    bless_sp = models.IntegerField(default=0)
    bless_p_atk = models.IntegerField(default=0)
    bless_p_def = models.IntegerField(default=0)
    bless_e_atk = models.IntegerField(default=0)
    bless_e_def = models.IntegerField(default=0)
    bless_crit = models.IntegerField(default=0)
    bless_spd = models.IntegerField(default=0)

    # Equipamiento
    current_weapon = models.CharField(max_length=100, blank=True, null=True)
    weapon_souls_count = models.IntegerField(default=0)
    current_armor = models.CharField(max_length=100, blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roster_entries'

    def __str__(self):
        return f"{self.traveler.name} - roster"