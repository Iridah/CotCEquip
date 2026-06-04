from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from api.models import Weapon, Armor, Accessory
from api.models.inventory import InventoryItem


def inventory_view(request):
    weapons     = Weapon.objects.all().order_by('name')
    headgear    = Armor.objects.filter(armor_group='Headgear').order_by('name')
    body_armor  = Armor.objects.filter(armor_group='Body Armor').order_by('name')
    accessories = Accessory.objects.all().order_by('name')

    owned_weapons     = set(InventoryItem.objects.filter(item_type='weapon').values_list('item_name', flat=True))
    owned_armors      = set(InventoryItem.objects.filter(item_type='armor').values_list('item_name', flat=True))
    owned_accessories = set(InventoryItem.objects.filter(item_type='accessory').values_list('item_name', flat=True))

    return render(request, 'inventory/inventory.html', {
        'weapons':          weapons,
        'headgear':         headgear,
        'body_armor':       body_armor,
        'accessories':      accessories,
        'owned_weapons':    owned_weapons,
        'owned_armors':     owned_armors,
        'owned_accessories': owned_accessories,
    })


@require_POST
def toggle_item(request):
    try:
        data      = json.loads(request.body)
        item_type = data.get('item_type')
        item_name = data.get('item_name')

        if not item_type or not item_name:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)

        if item_type not in ('weapon', 'armor', 'accessory'):
            return JsonResponse({'error': 'Tipo inválido'}, status=400)

        obj, created = InventoryItem.objects.get_or_create(
            item_type=item_type,
            item_name=item_name,
        )
        if not created:
            obj.delete()
            return JsonResponse({'owned': False})

        return JsonResponse({'owned': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)