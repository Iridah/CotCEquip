"""
rankings/calculator.py
Calcula scores PDPS, EDPS y Tankiness desde stats raw Lv.120
usando escala relativa por percentil.
"""

TIER_THRESHOLDS = [
    (95, 'S+'),
    (85, 'S'),
    (70, 'A'),
    (50, 'B'),
    (30, 'C'),
    (20, 'D'),
    (10, 'E'),
    (0,  'F'),
]

WEIGHTS = {
    'pdps':      {'p_atk_120': 0.65, 'crit_120': 0.35},
    'edps':      {'e_atk_120': 0.65, 'crit_120': 0.35},
    'tankiness': {'hp_120': 0.50, 'p_def_120': 0.25, 'e_def_120': 0.25},
}


def _score(traveler, weights):
    """Score compuesto ponderado para un traveler dado un set de pesos."""
    total = 0
    for field, weight in weights.items():
        val = getattr(traveler, field, None) or 0
        total += val * weight
    return total


def _percentile_rank(value, all_values):
    """Retorna el percentil de value dentro de all_values (0-100)."""
    if not all_values or value is None:
        return None
    below = sum(1 for v in all_values if v < value)
    return (below / len(all_values)) * 100


def _tier(percentile):
    if percentile is None:
        return 'n/a'
    for threshold, label in TIER_THRESHOLDS:
        if percentile >= threshold:
            return label
    return 'F'


def calculate_rankings(travelers):
    """
    Recibe queryset de Traveler.
    Retorna lista de dicts con name, sprite_url, job, element,
    rarity, pdps_score, edps_score, tankiness_score y sus tiers.
    """
    travelers = list(travelers)

    # Calcular scores crudos
    for t in travelers:
        t._pdps      = _score(t, WEIGHTS['pdps'])
        t._edps      = _score(t, WEIGHTS['edps'])
        t._tankiness = _score(t, WEIGHTS['tankiness'])

    pdps_vals      = [t._pdps      for t in travelers]
    edps_vals      = [t._edps      for t in travelers]
    tankiness_vals = [t._tankiness for t in travelers]

    results = []
    for t in travelers:
        # Verificar que tenga stats cargados
        has_stats = bool(t.hp_120 or t.p_atk_120 or t.e_atk_120)

        pdps_pct      = _percentile_rank(t._pdps,      pdps_vals)      if has_stats else None
        edps_pct      = _percentile_rank(t._edps,      edps_vals)      if has_stats else None
        tank_pct      = _percentile_rank(t._tankiness, tankiness_vals) if has_stats else None

        results.append({
            'name':           t.name,
            'sprite_url':     t.sprite_url,
            'job':            t.job,
            'element':        t.element,
            'rarity':         t.rarity,
            'pdps_tier':      _tier(pdps_pct),
            'edps_tier':      _tier(edps_pct),
            'tankiness_tier': _tier(tank_pct),
            'pdps_score':     round(t._pdps),
            'edps_score':     round(t._edps),
            'tankiness_score': round(t._tankiness),
        })

    # Ordenar por PDPS score descendente por defecto
    results.sort(key=lambda x: x['pdps_score'], reverse=True)
    return results