#!/usr/bin/env python3
"""
ingest_weapons_missing.py
Ingesta TODAS las secciones de weapons.txt (Lua del fandom).
Uso: python ingest_weapons_missing.py <weapons.txt>
"""
import re
import sys
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
            except:
                level = 1

            weapons.append({
                'name':        name,
                'weapon_type': weapon_type,
                'series':      '',
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

    for section_name, weapons in sections.items():
        print(f"\nProcesando {section_name}...")
        for w in weapons:
            if not w['name']:
                skipped += 1
                continue

            cur.execute("SELECT id FROM weapons WHERE name = %s", (w['name'],))
            exists = cur.fetchone()

            params = (
                w['weapon_type'], w['series'], w['level_req'],
                w['p_atk'], w['e_atk'], w['p_def'], w['e_def'],
                w['spd'], w['crit'], w['hp'], w['sp'],
                w['extra'], w['slot_count'],
            )

            if exists:
                cur.execute("""
                    UPDATE weapons SET
                        weapon_type=%s, series=%s, level_req=%s,
                        p_atk=%s, e_atk=%s, p_def=%s, e_def=%s,
                        spd=%s, crit=%s, hp=%s, sp=%s,
                        extra=%s, slot_count=%s
                    WHERE name=%s
                """, params + (w['name'],))
                updated += 1
            else:
                cur.execute("""
                    INSERT INTO weapons
                        (name, weapon_type, series, level_req,
                        p_atk, e_atk, p_def, e_def,
                        spd, crit, hp, sp, extra, slot_count)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (w['name'],) + params)
                inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✓ Insertadas: {inserted}")
    print(f"↺ Actualizadas: {updated}")
    print(f"✗ Saltadas: {skipped}")
    print(f"Total procesadas: {inserted + updated}")


if __name__ == '__main__':
    main()