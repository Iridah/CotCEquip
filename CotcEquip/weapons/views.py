from django.shortcuts import render
from api.models import Weapon

def weapons_view(request):
    weapons = Weapon.objects.all().order_by('weapon_type', 'level_req')
    
    weapon_types = Weapon.objects.values_list('weapon_type', flat=True).distinct().order_by('weapon_type')
    
    tipo    = request.GET.get('type', '').strip()
    q       = request.GET.get('q', '').strip()
    solo_soul = request.GET.get('solo_soul', '')

    if tipo:
        weapons = weapons.filter(weapon_type=tipo)
    if q:
        weapons = weapons.filter(name__icontains=q)
    if solo_soul:
        weapons = weapons.filter(is_soul_weapon=True)

    return render(request, 'weapons/weapons.html', {
        'weapons':      weapons,
        'weapon_types': weapon_types,
        'tipo':         tipo,
        'q':            q,
        'solo_soul':    solo_soul,
    })