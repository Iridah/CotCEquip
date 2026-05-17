#!/usr/bin/env python3
"""
ingest_weapons_lua.py - Importa las armas desde módulo Lua del fandom
Uso: python ingest_weapons_lua.py weapons.json
"""
import re
import sys
from pathlib import Path

from ingest_common import get_connection, parse_stat, clean_text

TYPE_MAP = {
    'Swords':  'Sword',
    'Polearms': 'Polearm',
    'Daggers': 'Dagger',
    'Axes':    'Axe',
    'Bows':    'Bow',
    'Staves':  'Staff',
    'Tomes':   'Tome',
    'Fans':    'Fan',
}

SOUL_SERIES = ['Cosmic', 'Thorned', 'Stalwart', 'Hollow', 'Dire', 'Abyssal', 'Arcane', 'Brilliant', 'Ruinous']

def detect_soul(name):
    for series in SOUL_SERIES:
        if series.lower() in name.lower():
            return True, series
    return False, ''

def parse_stat(val):
    if not val or val == '""':
        return 0
    val = str(val).strip().strip('"').replace('+', '').replace(',', '').strip()
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0

def parse_lua(filepath):
    text = Path(filepath).read_text(encoding='utf-8')
    weapons = []

    # Encontrar cada sección de tipo
    type_pattern = re.compile(r'(\w+)\s*=\s*\{', )
    weapon_pattern = re.compile(
        r'\["([^"]+)"\]\s*=\s*\{([^}]+)\}',
        re.DOTALL
    )
    field_pattern = re.compile(r'(\w+)\s*=\s*"([^"]*)"')

    current_type = None
    for match in re.finditer(r'(\w+)\s*=\s*\{', text):
        word = match.group(1)
        if word in TYPE_MAP:
            current_type = word

    # Parsear arma por arma con su tipo
    # Dividir el texto por secciones de tipo
    sections = re.split(r'\n\t(\w+)\s*=\s*\{', text)

    i = 0
    while i < len(sections):
        section = sections[i]
        type_name = None
        # Buscar si el siguiente token es un tipo conocido
        if i + 1 < len(sections) and sections[i+1] in TYPE_MAP:
            type_name = sections[i+1]
            content = sections[i+2] if i + 2 < len(sections) else ''
            i += 3
        else:
            i += 1
            continue

        weapon_type = TYPE_MAP[type_name]

        for wmatch in weapon_pattern.finditer(content):
            name = wmatch.group(1)
            body = wmatch.group(2)

            fields = dict(field_pattern.findall(body))

            is_soul, soul_series = detect_soul(name)

            weapons.append({
                'name':          name,
                'weapon_type':   weapon_type,
                'level_req':     parse_stat(fields.get('Level', '0')),
                'p_atk':         parse_stat(fields.get('Phys_Atk', '')),
                'e_atk':         parse_stat(fields.get('Elem_Atk', '')),
                'p_def':         parse_stat(fields.get('Phys_Def', '')),
                'e_def':         parse_stat(fields.get('Elem_Def', '')),
                'spd':           parse_stat(fields.get('Speed', '')),
                'crit':          parse_stat(fields.get('Critical', '')),
                'hp':            parse_stat(fields.get('Max_HP', '')),
                'sp':            parse_stat(fields.get('Max_SP', '')),
                'extra':         fields.get('Extra', '').replace('<br>', '\n').strip(),
                'is_soul':       is_soul,
                'soul_series':   soul_series,
            })

    return weapons

def main():
    if len(sys.argv) < 2:
        print("Uso: python ingest_weapons_lua.py <archivo>")
        sys.exit(1)

    print("Parseando Lua...")
    weapons = parse_lua(sys.argv[1])
    print(f"Armas encontradas: {len(weapons)}")

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    inserted = updated = skipped = 0

    for w in weapons:
        if not w['name']:
            skipped += 1
            continue

        cur.execute("SELECT id FROM weapons WHERE name = %s", (w['name'],))
        exists = cur.fetchone()

        params = (
            w['weapon_type'], w['level_req'],
            w['p_atk'], w['e_atk'], w['p_def'], w['e_def'],
            w['spd'], w['crit'], w['hp'], w['sp'],
            w['extra'], w['is_soul'], w['soul_series'],
        )

        if exists:
            cur.execute("""
                UPDATE weapons SET
                    weapon_type=%s, level_req=%s,
                    p_atk=%s, e_atk=%s, p_def=%s, e_def=%s,
                    spd=%s, crit=%s, hp=%s, sp=%s,
                    extra=%s, is_soul_weapon=%s, soul_series=%s
                WHERE name=%s
            """, params + (w['name'],))
            updated += 1
        else:
            cur.execute("""
                INSERT INTO weapons
                    (name, weapon_type, level_req,
                     p_atk, e_atk, p_def, e_def,
                     spd, crit, hp, sp,
                     extra, is_soul_weapon, soul_series)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (w['name'],) + params)
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"✓ Insertados: {inserted}")
    print(f"↺ Actualizados: {updated}")
    print(f"✗ Saltados: {skipped}")

if __name__ == '__main__':
    main()