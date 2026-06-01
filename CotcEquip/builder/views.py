from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_POST
 
from api.models import Traveler, Weapon, Armor, Accessory
from api.models.travelers import RosterEntry
 
 
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
    """
    Elige los n mejores accesorios distintos del catálogo general.
    Si hay trust accessory disponible, lo considera como candidato.
    Retorna lista de dicts con info del accesorio elegido.
    """
    # Construir pool con scores
    pool = []
    for acc in accessories:
        pool.append({
            'obj':      acc,
            'name':     acc.name,
            'score':    item_score(acc, stats_fields),
            'stats':    {f: getattr(acc, f, 0) or 0 for f in stats_fields},
            'extra':    acc.extra or '',
            'is_trust': False,
        })
 
    if trust:
        pool.append({
            'obj':      None,
            'name':     trust['name'],
            'score':    trust['score'],
            'stats':    trust['stats'],
            'extra':    trust['extra'],
            'is_trust': True,
        })
 
    # Ordenar por score descendente, tomar los mejores n distintos
    pool.sort(key=lambda x: x['score'], reverse=True)
    chosen = []
    seen = set()
    for item in pool:
        if item['name'] not in seen:
            chosen.append(item)
            seen.add(item['name'])
        if len(chosen) == n:
            break
 
    return chosen
 
 
def optimize(traveler, entry, objective_key):
    stats_fields = OBJECTIVES[objective_key][1]
 
    weapons     = list(Weapon.objects.all())
    headgear    = list(Armor.objects.filter(armor_group='Headgear'))
    body_armor  = list(Armor.objects.filter(armor_group='Body Armor'))
    accessories = list(Accessory.objects.all())
 
    # Trust accessory
    trust = None
    if entry and entry.awakening_level >= 4 and traveler.trust_acc_name:
        trust = {
            'name':  traveler.trust_acc_name,
            'score': trust_score(traveler, stats_fields),
            'stats': {f: getattr(traveler, f'trust_acc_{f}', 0) or 0
                      for f in stats_fields},
            'extra': traveler.trust_acc_extra or '',
        }
 
    # Slots de accesorio según roster
    acc_slots = 2  # default
    if entry and entry.is_6_stars:
        acc_slots = 3
 
    # Mejor weapon
    best_w = max(weapons, key=lambda w: item_score(w, stats_fields))
 
    # Mejor headgear y body armor por separado
    best_hg = max(headgear,   key=lambda a: item_score(a, stats_fields)) if headgear   else None
    best_ba = max(body_armor, key=lambda a: item_score(a, stats_fields)) if body_armor else None
 
    # Mejores accesorios
    chosen_accs = best_n_accessories(accessories, trust, acc_slots, stats_fields)
 
    # Calcular scores
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
 
    base_score = sum(STAT_MAP.get(f, 0) for f in stats_fields)
 
    equip_score = (
        item_score(best_w,  stats_fields) +
        (item_score(best_hg, stats_fields) if best_hg else 0) +
        (item_score(best_ba, stats_fields) if best_ba else 0) +
        sum(a['score'] for a in chosen_accs)
    )
 
    return {
        'objective':   OBJECTIVES[objective_key][0],
        'weapon':      best_w,
        'headgear':    best_hg,
        'body_armor':  best_ba,
        'accessories': chosen_accs,
        'acc_slots':   acc_slots,
        'base_score':  base_score,
        'equip_score': equip_score,
        'total_score': base_score + equip_score,
        'stats_fields': stats_fields,
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
 
    if not traveler_id:
        return HttpResponse('<p class="text-muted">Seleccioná un traveler.</p>')
 
    try:
        traveler = Traveler.objects.get(pk=traveler_id)
    except Traveler.DoesNotExist:
        return HttpResponse('<p class="text-danger">Traveler no encontrado.</p>')
 
    try:
        entry = RosterEntry.objects.get(traveler=traveler)
    except RosterEntry.DoesNotExist:
        entry = None
 
    if objective not in OBJECTIVES:
        objective = 'e_atk'
 
    result = optimize(traveler, entry, objective)
 
    return render(request, 'builder/partials/result.html', {
        'traveler': traveler,
        'result':   result,
        'entry':    entry,
    })
 
# ── Vista optimizador con soporte modal (JSON) ────────────────────────────────
# Reemplazar el @require_POST optimize_view existente por este:
 
from django.http import JsonResponse
 
@require_POST
def optimize_view(request):
    traveler_id = request.POST.get('traveler_id')
    objective   = request.POST.get('objective', 'e_atk')
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
 
    result = optimize(traveler, entry, objective)
 
    # Respuesta JSON para el modal
    if is_modal:
        return JsonResponse({
            'weapon':     result['weapon'].name,
            'headgear':   result['headgear'].name if result['headgear'] else '',
            'body_armor': result['body_armor'].name if result['body_armor'] else '',
            'accessories': [a['name'] for a in result['accessories']],
            'total_score': result['total_score'],
        })
 
    # Respuesta HTML para el builder standalone
    return render(request, 'builder/partials/result.html', {
        'traveler': traveler,
        'result':   result,
        'entry':    entry,
    })