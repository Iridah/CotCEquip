#!/usr/bin/env python3
"""
ingest_weapons_missing.py
Ingesta TODAS las secciones de weapons.txt (Lua del fandom).
Uso: python ingest_weapons_missing.py <weapons.txt>

Reglas de negocio:
- series / arc: si ya tiene valor en BD → no tocar.
                Si vacío → dejar vacío, EXCEPTO prefijos conocidos de Osterra
                (Cosmic*, Stamp*, Ballen*, *Fortune*) que se marcan 'Osterra'.
- soul_bonus_1..4: nunca se tocan (se pueblan desde Notion).
- req_mat: columna text en BD, se guarda como JSON string.
- arc: misma lógica que series.
"""
import re
import sys
import json
from pathlib import Path

import psycopg2

DB_CONFIG = {
    'dbname':   'cotc_db',
    'user':     'cotc_user',
    'password': '***PURGED-DB-PASSWORD***',
    'host':     '127.0.0.1',
    'port':     5432,
}

ALL_SECTIONS = {
    'Swords':   'Sword',
    'Polearms': 'Polearm',
    'Daggers':  'Dagger',
    'Axes':     'Axe',
    'Bows':     'Bow',
    'Staves':   'Staff',
    'Tomes':    'Tome',
    'Fans':     'Fan',
}

PLACEHOLDER = {'Weapon Name'}

# Prefijos/patrones que sabemos con certeza que son Osterra
OSTERRA_PATTERNS = re.compile(
    r'^(Cosmic|Stamp|Ballen|Brave)|Fortune',
    re.IGNORECASE
)


def infer_arc(name: str) -> str:
    """Devuelve 'Osterra' si el nombre coincide con patrones conocidos, sino ''."""
    if OSTERRA_PATTERNS.search(name):
        return 'Osterra'
    return ''


def parse_stat(val):
    if not val:
        return 0
    val = str(val).strip().replace('+', '').replace(',', '')
    try:
        return int(val)
    except ValueError:
        return 0


def clean_text(val):
    if not val:
        return ''
    return str(val).strip()


def parse_req_mat(raw: str) -> list:
    """
    Convierte "Item A x5<br>Item B x2" → ["Item A x5", "Item B x2"]
    Devuelve lista vacía si no hay materiales.
    """
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r'<br\s*/?>', raw, flags=re.IGNORECASE)]
    return [p for p in parts if p]


def parse_lua(filepath):
    text = Path(filepath).read_text(encoding='utf-8')
    results = {}

    section_re = re.compile(r'\t(\w+)\s*=\s*\{', re.MULTILINE)
    sections = list(section_re.finditer(text))

    for i, m in enumerate(sections):
        section_name = m.group(1)
        if section_name not in ALL_SECTIONS:
            continue

        start = m.end()
        end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
        block = text[start:end]

        weapon_type = ALL_SECTIONS[section_name]
        weapons = []
        seen = set()

        item_re = re.compile(r'\["([^"]+)"\]\s*=\s*\{([^}]*)\}', re.DOTALL)
        str_re  = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
        num_re  = re.compile(r'(\w+)\s*=\s*(-?\d+)')

        for item_m in item_re.finditer(block):
            name = item_m.group(1).strip()
            body = item_m.group(2)

            if name in PLACEHOLDER or name in seen:
                continue
            seen.add(name)

            fields_str = dict(str_re.findall(body))
            fields_num = dict(num_re.findall(body))

            def get(key):
                v = fields_str.get(key, '')
                return parse_stat(v) if v else parse_stat(fields_num.get(key, ''))

            try:
                level = int(fields_num.get('Level', 1))
            except Exception:
                level = 1

            req_mat_raw = fields_str.get('Req_Mat', '')
            req_mat_list = parse_req_mat(req_mat_raw)

            weapons.append({
                'name':        name,
                'weapon_type': weapon_type,
                'inferred_arc': infer_arc(name),  # 'Osterra' o ''
                'level_req':   level,
                'p_atk':       get('Phys_Atk'),
                'e_atk':       get('Elem_Atk'),
                'p_def':       get('Phys_Def'),
                'e_def':       get('Elem_Def'),
                'spd':         get('Speed'),
                'crit':        get('Critical'),
                'hp':          get('Max_HP'),
                'sp':          get('Max_SP'),
                'extra':       clean_text(fields_str.get('Extra', '')),
                'slot_count':  0,
                'req_mat':     req_mat_list,
            })

        results[section_name] = weapons
        print(f"  {section_name}: {len(weapons)} armas parseadas")

    return results


def main():
    if len(sys.argv) < 2:
        print("Uso: python ingest_weapons_missing.py <weapons.txt>")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"Parseando {filepath}...")
    sections = parse_lua(filepath)

    total_weapons = sum(len(v) for v in sections.values())
    print(f"Total armas a ingestar: {total_weapons}")

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    inserted = updated = skipped = 0
    arc_tagged = 0

    for section_name, weapons in sections.items():
        print(f"\nProcesando {section_name}...")
        for w in weapons:
            if not w['name']:
                skipped += 1
                continue

            # Leer estado actual de series y arc en BD
            cur.execute(
                "SELECT id, series, arc FROM weapons WHERE name = %s",
                (w['name'],)
            )
            row = cur.fetchone()

            req_mat_json = json.dumps(w['req_mat'], ensure_ascii=False)

            # Respetar series/arc existentes; solo escribir si están vacíos
            # y tenemos inferencia confiable
            if row:
                existing_id, existing_series, existing_arc = row

                new_series = existing_series if existing_series else ''
                new_arc    = existing_arc    if existing_arc    else w['inferred_arc']

                if not existing_arc and w['inferred_arc']:
                    arc_tagged += 1

                cur.execute("""
                    UPDATE weapons SET
                        weapon_type = %s,
                        series      = %s,
                        arc         = %s,
                        level_req   = %s,
                        p_atk=%s, e_atk=%s, p_def=%s, e_def=%s,
                        spd=%s, crit=%s, hp=%s, sp=%s,
                        extra=%s, slot_count=%s,
                        req_mat=%s
                    WHERE id = %s
                """, (
                    w['weapon_type'],
                    new_series,
                    new_arc,
                    w['level_req'],
                    w['p_atk'], w['e_atk'], w['p_def'], w['e_def'],
                    w['spd'], w['crit'], w['hp'], w['sp'],
                    w['extra'], w['slot_count'],
                    req_mat_json,
                    existing_id,
                ))
                updated += 1

            else:
                # INSERT — series vacío, arc inferido si aplica
                if w['inferred_arc']:
                    arc_tagged += 1

                cur.execute("""
                    INSERT INTO weapons
                        (name, weapon_type, series, arc, level_req,
                         p_atk, e_atk, p_def, e_def,
                         spd, crit, hp, sp, extra, slot_count, req_mat)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    w['name'],
                    w['weapon_type'],
                    '',                   # series vacío
                    w['inferred_arc'],    # arc inferido o ''
                    w['level_req'],
                    w['p_atk'], w['e_atk'], w['p_def'], w['e_def'],
                    w['spd'], w['crit'], w['hp'], w['sp'],
                    w['extra'], w['slot_count'],
                    req_mat_json,
                ))
                inserted += 1

    conn.commit()

    # Resumen post-ingesta
    cur.execute("""
        SELECT
            COUNT(*)                                                AS total,
            COUNT(*) FILTER (WHERE req_mat IS NOT NULL
                             AND req_mat != '[]')                  AS con_mat,
            COUNT(*) FILTER (WHERE req_mat IS NULL
                             OR  req_mat  = '[]')                  AS sin_mat,
            COUNT(*) FILTER (WHERE arc = 'Osterra')                AS osterra,
            COUNT(*) FILTER (WHERE arc = 'Solistia')               AS solistia,
            COUNT(*) FILTER (WHERE arc = 'Unchosen')               AS unchosen,
            COUNT(*) FILTER (WHERE arc IS NULL OR arc = '')        AS sin_arc
        FROM weapons
    """)
    stats = cur.fetchone()

    cur.close()
    conn.close()

    print(f"\n✓ Insertadas : {inserted}")
    print(f"↺ Actualizadas: {updated}")
    print(f"✗ Saltadas   : {skipped}")
    print(f"🏷  Arc tagged : {arc_tagged} (esta corrida)")
    print(f"\n── Estado BD post-ingesta ──")
    print(f"  Total weapons : {stats[0]}")
    print(f"  Con req_mat   : {stats[1]}")
    print(f"  Sin req_mat   : {stats[2]}  ← base/canje directo, esperado")
    print(f"  Osterra       : {stats[3]}")
    print(f"  Solistia      : {stats[4]}")
    print(f"  Unchosen      : {stats[5]}")
    print(f"  Sin arc       : {stats[6]}  ← pendiente clasificar")


if __name__ == '__main__':
    main()