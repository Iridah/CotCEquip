from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from api.models.travelers import RosterEntry
from api.models.inventory import InventoryItem
from api.models import Traveler, Weapon, Armor, Accessory, TravelerSkill


OBJECTIVES = {
    'p_atk':      ('P.Atk',         ['p_atk']),
    'e_atk':      ('E.Atk',         ['e_atk']),
    'p_def':      ('P.Def',         ['p_def']),
    'e_def':      ('E.Def',         ['e_def']),
    'tankiness':  ('P.Def + E.Def', ['p_def', 'e_def']),
    'p_atk_crit': ('P.Atk + Crit',  ['p_atk', 'crit']),
    'e_atk_crit': ('E.Atk + Crit',  ['e_atk', 'crit']),
    'spd':        ('Velocidad',      ['spd']),
    'hp':         ('HP',             ['hp']),
}


def item_score(obj, stats_fields):
    return sum(getattr(obj, f, 0) or 0 for f in stats_fields)


def trust_score(traveler, stats_fields):
    return sum(getattr(traveler, f'trust_acc_{f}', 0) or 0 for f in stats_fields)


def best_n_accessories(accessories, trust, n, stats_fields):
    pool = []
    for acc in accessories:
        pool.append({
            'obj':         acc,
            'name':        acc.name,
            'score':       item_score(acc, stats_fields),
            'stats':       {f: getattr(acc, f, 0) or 0 for f in stats_fields},
            'extra':       acc.extra or '',
            'is_trust':    False,
            'is_artifact': getattr(acc, 'is_artifact', False),
        })

    if trust:
        pool.append({
            'obj':         None,
            'name':        trust['name'],
            'score':       trust['score'],
            'stats':       trust['stats'],
            'extra':       trust['extra'],
            'is_trust':    True,
            'is_artifact': False,
        })

    pool.sort(key=lambda x: x['score'], reverse=True)
    chosen = []
    seen = set()
    artifact_used = False

    for item in pool:
        if item['name'] in seen:
            continue
        if item['is_artifact']:
            if artifact_used:
                continue
            artifact_used = True
        chosen.append(item)
        seen.add(item['name'])
        if len(chosen) == n:
            break

    return chosen


def _get_inventory_sets():
    owned_weapons     = set()
    owned_armors      = set()
    owned_accessories = set()
    for item in InventoryItem.objects.values('item_type', 'item_name'):
        if item['item_type'] == 'weapon':
            owned_weapons.add(item['item_name'])
        elif item['item_type'] == 'armor':
            owned_armors.add(item['item_name'])
        elif item['item_type'] == 'accessory':
            owned_accessories.add(item['item_name'])
    return owned_weapons, owned_armors, owned_accessories


def optimize(traveler, entry, objective_key, data_source='all', arc='all'):
    stats_fields = OBJECTIVES[objective_key][1]

    if data_source == 'roster':
        owned_w, owned_a, owned_acc = _get_inventory_sets()
        weapons    = list(Weapon.objects.filter(name__in=owned_w))                          if owned_w   else list(Weapon.objects.all())
        headgear   = list(Armor.objects.filter(armor_group='Headgear',   name__in=owned_a)) if owned_a   else list(Armor.objects.filter(armor_group='Headgear'))
        body_armor = list(Armor.objects.filter(armor_group='Body Armor', name__in=owned_a)) if owned_a   else list(Armor.objects.filter(armor_group='Body Armor'))
        acc_qs     = Accessory.objects.filter(name__in=owned_acc)                           if owned_acc else Accessory.objects.all()
    else:
        weapons    = list(Weapon.objects.all())
        headgear   = list(Armor.objects.filter(armor_group='Headgear'))
        body_armor = list(Armor.objects.filter(armor_group='Body Armor'))
        acc_qs     = Accessory.objects.all()

    # Filtro de arco en weapons y armors
    if arc and arc != 'all':
        weapons    = [w for w in weapons    if getattr(w, 'arc', None) == arc]
        headgear   = [a for a in headgear   if getattr(a, 'arc', None) == arc]
        body_armor = [a for a in body_armor if getattr(a, 'arc', None) == arc]

    # Filtro de exclusivos e imprints
    traveler_weapon_types = set(
        w.strip() for w in (traveler.weapon_types or traveler.weapon_type or '').split(',')
        if w.strip()
    )
    traveler_element = (traveler.element or '').strip()

    accessories = [
        a for a in acc_qs
        if not a.is_exclusive or a.exclusive_traveler == traveler.name
        if not a.imprint_req or (
            a.imprint_req in traveler_weapon_types or
            a.imprint_req == traveler_element
        )
    ]

    # Trust accessory — pendiente modelar en travelers_master
    trust = None

    acc_slots = 3 if (entry and entry.is_6_stars) else 2

    best_w  = max(weapons,    key=lambda w: item_score(w, stats_fields)) if weapons    else None
    best_hg = max(headgear,   key=lambda a: item_score(a, stats_fields)) if headgear   else None
    best_ba = max(body_armor, key=lambda a: item_score(a, stats_fields)) if body_armor else None

    chosen_accs = best_n_accessories(accessories, trust, acc_slots, stats_fields)

    STAT_MAP = {
        'p_atk': traveler.p_atk_120,
        'e_atk': traveler.e_atk_120,
        'p_def': traveler.p_def_120,
        'e_def': traveler.e_def_120,
        'spd':   traveler.spd_120,
        'crit':  traveler.crit_120,
        'hp':    traveler.hp_120,
        'sp':    traveler.sp_120,
    }

    base_score  = sum(STAT_MAP.get(f, 0) for f in stats_fields)
    equip_score = (
        (item_score(best_w,  stats_fields) if best_w  else 0) +
        (item_score(best_hg, stats_fields) if best_hg else 0) +
        (item_score(best_ba, stats_fields) if best_ba else 0) +
        sum(a['score'] for a in chosen_accs)
    )

    # Sumar stat_bonus de skills pasivas
    skill_bonus = {}
    for skill in TravelerSkill.objects.filter(
        traveler=traveler,
        skill_type__in=['passive', 'ex']
    ).exclude(stat_bonus={}):
        for key, val in skill.stat_bonus.items():
            skill_bonus[key] = skill_bonus.get(key, 0) + val

    # Agregar damage_limit al resultado si existe
    damage_limit_bonus = skill_bonus.get('damage_limit', 0)

    return {
        'objective':    OBJECTIVES[objective_key][0],
        'weapon':       best_w,
        'headgear':     best_hg,
        'body_armor':   best_ba,
        'accessories':  chosen_accs,
        'acc_slots':    acc_slots,
        'base_score':   base_score,
        'equip_score':  equip_score,
        'total_score':  base_score + equip_score,
        'stats_fields': stats_fields,
        'data_source':  data_source,
        'skill_bonus':  skill_bonus,
        'damage_limit_bonus': damage_limit_bonus,
    }


def builder_view(request):
    travelers = Traveler.objects.all().order_by('name')
    return render(request, 'builder/builder.html', {
        'travelers':  travelers,
        'objectives': OBJECTIVES,
    })


@require_POST
def optimize_view(request):
    traveler_id = request.POST.get('traveler_id')
    objective   = request.POST.get('objective', 'e_atk')
    data_source = request.POST.get('data_source', 'all')
    arc         = request.POST.get('arc', 'all')
    is_modal    = request.headers.get('X-Modal-Request') == '1'

    if not traveler_id:
        if is_modal:
            return JsonResponse({'error': 'Sin traveler'}, status=400)
        return HttpResponse('<p class="text-muted">Seleccioná un traveler.</p>')

    try:
        traveler = Traveler.objects.get(pk=traveler_id)
    except Traveler.DoesNotExist:
        if is_modal:
            return JsonResponse({'error': 'No encontrado'}, status=404)
        return HttpResponse('<p class="text-danger">Traveler no encontrado.</p>')

    try:
        entry = RosterEntry.objects.get(traveler=traveler)
    except RosterEntry.DoesNotExist:
        entry = None

    if objective not in OBJECTIVES:
        objective = 'e_atk'

    result = optimize(traveler, entry, objective, data_source, arc)

    # Sugerencias — solo cuando el usuario usa su roster
    suggestions = None
    if data_source == 'roster':
        result_all = optimize(traveler, entry, objective, 'all', arc)

        current_names = set()
        if result['weapon']:
            current_names.add(result['weapon'].name)
        if result['headgear']:
            current_names.add(result['headgear'].name)
        if result['body_armor']:
            current_names.add(result['body_armor'].name)
        current_names.update(a['name'] for a in result['accessories'])

        suggestions = {
            'weapon':      result_all['weapon']     if result_all['weapon']     and result_all['weapon'].name     not in current_names else None,
            'headgear':    result_all['headgear']   if result_all['headgear']   and result_all['headgear'].name   not in current_names else None,
            'body_armor':  result_all['body_armor'] if result_all['body_armor'] and result_all['body_armor'].name not in current_names else None,
            'accessories': [a for a in result_all['accessories'] if a['name'] not in current_names],
            'score_delta': result_all['total_score'] - result['total_score'],
            'stats_fields': result_all['stats_fields'],
        }

    if is_modal:
        return JsonResponse({
            'weapon':      result['weapon'].name if result['weapon'] else '',
            'headgear':    result['headgear'].name if result['headgear'] else '',
            'body_armor':  result['body_armor'].name if result['body_armor'] else '',
            'accessories': [a['name'] for a in result['accessories']],
            'total_score': result['total_score'],
        })

    return render(request, 'builder/partials/result.html', {
        'traveler':    traveler,
        'result':      result,
        'entry':       entry,
        'suggestions': suggestions,
    })