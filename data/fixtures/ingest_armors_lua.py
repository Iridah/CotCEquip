#!/usr/bin/env python3
"""
ingest_armors_lua.py - Importa armaduras desde módulo Lua del fandom
Uso: python ingest_armors_lua.py <Armors.txt>
 
armor_group : Headgear | Body Armor  (categoría del wiki)
armor_type  : Hood, Robe, Helm, etc. (inferido del nombre)
"""
import re
import sys
from pathlib import Path
 
from ingest_common import get_connection, parse_stat, clean_text
 
ARMOR_GROUPS = ['Headgear', 'Body Armor']
PLACEHOLDERS = {'Armor Name'}
 
TYPE_TOKENS = [
    'bandana', 'hood', 'cap', 'hat', 'helm',
    'robe', 'vest', 'armor', 'mail', 'chainmail',
    'coat', 'garb', 'garment', 'knitwear', 'kimono',
    'attire',
]
 
 
def detect_armor_type(name):
    name_l = name.lower()
    for token in TYPE_TOKENS:
        if token in name_l:
            return token.title()
    return 'Other'
 
 
def parse_lua(filepath):
    text = Path(filepath).read_text(encoding='utf-8')
    armors = []
 
    item_re = re.compile(r'\t\t\["([^"]+)"\]\s*=\s*\{([^}]*)\}', re.DOTALL)
    str_re  = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
    num_re  = re.compile(r'(\w+)\s*=\s*(-?\d+)')
 
    # Localizar posición de cada grupo para seccionar el texto
    type_positions = []
    for g in ARMOR_GROUPS:
        pat = re.compile(rf'\["{re.escape(g)}"\]\s*=\s*\{{')
        m = pat.search(text)
        if m:
            type_positions.append((m.start(), g))
    type_positions.sort(key=lambda x: x[0])
 
    seen = set()
 
    for idx, (pos, armor_group) in enumerate(type_positions):
        end_pos = type_positions[idx + 1][0] if idx + 1 < len(type_positions) else len(text)
        section = text[pos:end_pos]
 
        for m in item_re.finditer(section):
            name = m.group(1).strip()
            body = m.group(2)
 
            if name in PLACEHOLDERS or name == armor_group:
                continue
            if name in seen:
                continue
            seen.add(name)
 
            fields_str = dict(str_re.findall(body))
            fields_num = dict(num_re.findall(body))
 
            def get(key):
                v = fields_str.get(key, '')
                return parse_stat(v) if v else parse_stat(fields_num.get(key, ''))
 
            armors.append({
                'name':        name,
                'armor_group': armor_group,
                'armor_type':  detect_armor_type(name),
                'p_def':       get('Phys_Def'),
                'e_def':       get('Elem_Def'),
                'p_atk':       get('Phys_Atk'),
                'e_atk':       get('Elem_Atk'),
                'spd':         get('Speed'),
                'crit':        get('Critical'),
                'hp':          get('Max_HP'),
                'sp':          get('Max_SP'),
                'extra':       clean_text(fields_str.get('Extra', '')),
            })
 
    return armors
 
 
def main():
    if len(sys.argv) < 2:
        print("Uso: python ingest_armors_lua.py <Armors.txt>")
        sys.exit(1)
 
    print("Parseando Lua...")
    items = parse_lua(sys.argv[1])
    print(f"Armaduras encontradas: {len(items)}")
    by_group = {}
    for a in items:
        by_group[a['armor_group']] = by_group.get(a['armor_group'], 0) + 1
    for g, n in sorted(by_group.items()):
        print(f"  {g}: {n}")
 
    conn = get_connection()
    cur  = conn.cursor()
 
    inserted = updated = skipped = 0
 
    for a in items:
        if not a['name']:
            skipped += 1
            continue
 
        cur.execute("SELECT id FROM armors WHERE name = %s", (a['name'],))
        exists = cur.fetchone()
 
        params = (
            a['armor_group'], a['armor_type'],
            a['p_def'], a['e_def'],
            a['p_atk'], a['e_atk'],
            a['spd'], a['crit'],
            a['hp'], a['sp'],
            a['extra'],
        )
 
        if exists:
            cur.execute("""
                UPDATE armors SET
                    armor_group=%s, armor_type=%s,
                    p_def=%s, e_def=%s,
                    p_atk=%s, e_atk=%s,
                    spd=%s, crit=%s,
                    hp=%s, sp=%s,
                    extra=%s
                WHERE name=%s
            """, params + (a['name'],))
            updated += 1
        else:
            cur.execute("""
                INSERT INTO armors
                    (name, armor_group, armor_type,
                     p_def, e_def,
                     p_atk, e_atk,
                     spd, crit,
                     hp, sp,
                     extra)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (a['name'],) + params)
            inserted += 1
 
    conn.commit()
    cur.close()
    conn.close()
 
    print(f"✓ Insertados: {inserted}")
    print(f"↺ Actualizados: {updated}")
    print(f"✗ Saltados: {skipped}")
 
 
if __name__ == '__main__':
    main()