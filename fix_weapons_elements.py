"""
fix_weapons_elements.py
Corrige weapon_type y agrega element en travelers_master usando el CSV original.

Uso:
    python fix_weapons_elements.py

Requiere: psycopg2, csv original en la ruta indicada
"""

import csv
import re
import os
from urllib.parse import unquote

# ── Configuración ─────────────────────────────────────────────────────────────
CSV_PATH = os.path.expanduser('~/Programacion/CotCEquip/data/fixtures/Character List 306de07ed2d5816c9391e35e834b78d6_all.csv')

DB_CONFIG = {
    'dbname':   'cotc_db',
    'user':     'cotc_user',
    'password': 'ShWRmx6eBmPubZve7GKidkjPeMbd9fUv3iHe',
    'host':     '127.0.0.1',
    'port':     5432,
}

# ── Mapeo de nombres de archivo → valores limpios ─────────────────────────────
WEAPON_MAP = {
    'Sword':        'Sword',
    'Dagger':       'Dagger',
    'Axe':          'Axe',
    'Bow':          'Bow',
    'Staff':        'Staff',
    'Staff_Staves': 'Staff',
    'Spear_Polearm':'Polearm',
    'Polearm':      'Polearm',
    'Fan':          'Fan',
    'Tome':         'Tome',
}

ELEMENT_MAP = {
    'Fire':               'Fire',
    'Ice':                'Ice',
    'Lightning':          'Lightning',
    'Lightning_Thunder':  'Lightning',
    'Wind':               'Wind',
    'Light':              'Light',
    'Dark':               'Dark',
}

ELEMENT_KEYWORDS = set(ELEMENT_MAP.keys())
WEAPON_KEYWORDS  = set(WEAPON_MAP.keys())


def parse_attributes(attrs_raw):
    """
    Dado el campo Attributes (URLs de imágenes separadas por coma),
    retorna (weapon_primary, element, weapon_types_list).
    """
    decoded = unquote(attrs_raw)
    files   = re.findall(r'/([^/]+)\.png', decoded)

    weapons  = []
    elements = []

    for fname in files:
        clean = re.sub(r'\s*\d+$', '', fname).strip()
        if clean in WEAPON_KEYWORDS:
            weapons.append(WEAPON_MAP[clean])
        elif clean in ELEMENT_KEYWORDS:
            elements.append(ELEMENT_MAP[clean])

    weapon_primary = weapons[0] if weapons else 'Unknown'
    element        = elements[0] if elements else 'None'
    weapon_types   = ', '.join(dict.fromkeys(weapons))  # únicos, orden preservado

    return weapon_primary, element, weapon_types


def main():
    import psycopg2

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    # 1. Agregar columnas si no existen
    print("Verificando columnas...")
    cur.execute("""
        ALTER TABLE travelers_master
            ADD COLUMN IF NOT EXISTS element      VARCHAR(20) DEFAULT 'None',
            ADD COLUMN IF NOT EXISTS weapon_types VARCHAR(100) DEFAULT '';
    """)
    conn.commit()
    print("  ✓ Columnas verificadas.")

    # 2. Leer CSV y actualizar
    updated = 0
    skipped = 0

    with open(CSV_PATH, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row  = {k.strip(): v for k, v in row.items() if k}
            name = (row.get('Name') or '').strip()
            if not name:
                continue

            attrs = row.get('Attributes', '')
            if not attrs.strip():
                skipped += 1
                continue

            weapon_primary, element, weapon_types = parse_attributes(attrs)

            cur.execute("""
                UPDATE travelers_master
                SET
                    weapon_type  = %s,
                    element      = %s,
                    weapon_types = %s
                WHERE name = %s
            """, (weapon_primary, element, weapon_types, name))

            if cur.rowcount > 0:
                updated += 1
            else:
                print(f"  ⚠ No encontrado en BD: {repr(name)}")
                skipped += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✓ Completado: {updated} actualizados, {skipped} saltados.")


if __name__ == '__main__':
    main()
