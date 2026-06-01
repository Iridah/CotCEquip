#!/usr/bin/env python3
"""
ingest_accessories_lua.py - Importa accesorios desde módulo Lua del fandom
Uso: python ingest_accessories_lua.py <Accesories.txt>
"""
import re
import sys
from pathlib import Path
 
from ingest_common import get_connection, parse_stat, clean_text
 
PLACEHOLDER = {'Accessory Name'}
 
 
def parse_lua(filepath):
    text = Path(filepath).read_text(encoding='utf-8')
    accessories = []
 
    item_re = re.compile(r'\t\["([^"]+)"\]\s*=\s*\{([^}]*)\}', re.DOTALL)
    str_re  = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
    num_re  = re.compile(r'(\w+)\s*=\s*(-?\d+)')
 
    seen = set()
 
    for m in item_re.finditer(text):
        name = m.group(1).strip()
        body = m.group(2)
 
        if name in PLACEHOLDER:
            continue
        if name in seen:
            continue
        seen.add(name)
 
        fields_str = dict(str_re.findall(body))
        fields_num = dict(num_re.findall(body))
 
        def get(key):
            v = fields_str.get(key, '')
            return parse_stat(v) if v else parse_stat(fields_num.get(key, ''))
 
        accessories.append({
            'name':  name,
            'is_a4': False,
            'p_atk': get('Phys_Atk'),
            'e_atk': get('Elem_Atk'),
            'p_def': get('Phys_Def'),
            'e_def': get('Elem_Def'),
            'spd':   get('Speed'),
            'crit':  get('Critical'),
            'hp':    get('Max_HP'),
            'sp':    get('Max_SP'),
            'extra': clean_text(fields_str.get('Extra', '')),
        })
 
    return accessories
 
 
def main():
    if len(sys.argv) < 2:
        print("Uso: python ingest_accessories_lua.py <Accesories.txt>")
        sys.exit(1)
 
    print("Parseando Lua...")
    items = parse_lua(sys.argv[1])
    print(f"Accessories encontrados: {len(items)}")
 
    conn = get_connection()
    cur  = conn.cursor()
 
    inserted = updated = skipped = 0
 
    for a in items:
        if not a['name']:
            skipped += 1
            continue
 
        cur.execute("SELECT id FROM accessories WHERE name = %s", (a['name'],))
        exists = cur.fetchone()
 
        params = (
            a['p_atk'], a['e_atk'], a['p_def'], a['e_def'],
            a['spd'], a['crit'], a['hp'], a['sp'],
            a['extra'],
        )
 
        if exists:
            cur.execute("""
                UPDATE accessories SET
                    p_atk=%s, e_atk=%s, p_def=%s, e_def=%s,
                    spd=%s, crit=%s, hp=%s, sp=%s,
                    extra=%s
                WHERE name=%s
            """, params + (a['name'],))
            updated += 1
        else:
            cur.execute("""
                INSERT INTO accessories
                    (name, is_a4,
                     p_atk, e_atk, p_def, e_def,
                     spd, crit, hp, sp, extra)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (a['name'], a['is_a4']) + params)
            inserted += 1
 
    conn.commit()
    cur.close()
    conn.close()
 
    print(f"✓ Insertados: {inserted}")
    print(f"↺ Actualizados: {updated}")
    print(f"✗ Saltados: {skipped}")
 
 
if __name__ == '__main__':
    main()