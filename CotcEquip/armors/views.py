from django.shortcuts import render
from api.models import Armor
 
def armors_view(request):
    armors = Armor.objects.all().order_by('armor_group', 'name')
 
    armor_groups = Armor.objects.values_list('armor_group', flat=True).distinct().order_by('armor_group')
 
    grupo = request.GET.get('group', '').strip()
    q     = request.GET.get('q', '').strip()
 
    if grupo:
        armors = armors.filter(armor_group=grupo)
    if q:
        armors = armors.filter(name__icontains=q)
 
    return render(request, 'armors/armors.html', {
        'armors':       armors,
        'armor_groups': armor_groups,
        'grupo':        grupo,
        'q':            q,
    })