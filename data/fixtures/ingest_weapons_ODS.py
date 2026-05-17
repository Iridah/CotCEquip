#!/usr/bin/env python3
"""
ingest_weapons.py - Importa armas desde ODS a la tabla weapons
Uso: python ingest_weapons.py "Armas_CotC_Cap1.ods"
"""
import csv
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

import environ
import pandas as pd
import psycopg2

env = environ.Env()
environ.Env.read_env(Path(__file__).resolve().parent.parent.parent / 'CotcEquip' / '.env')

DB_CONFIG = {
    'dbname':   env('DB_NAME'),
    'user':     env('DB_USER'),
    'password': env('DB_PASSWORD'),
    'host':     env('DB_HOST'),
    'port':     5432,
}

TYPE_MAP = {
    'Spear': 'Polearm',  # normalizar al nombre que usa la BD
}

SOUL_SERIES = ['Cosmic', 'Thorned', 'Stalwart', 'Hollow', 'Dire', 'Abyssal', 'Arcane', 'Brilliant', 'Ruinous']

def detect_soul(name):
    for series in SOUL_SERIES:
        if series.lower() in name.lower():
            return True, series
    return False, ''

def parse_int(val):
    try:
        v = int(str(val).replace(',', '').strip())
        return v if v != 0 else 0
    except (ValueError, TypeError):
        return 0

def main():
    if len(sys.argv) < 2:
        print("Uso: python ingest_weapons.py <archivo.ods>")
        sys.exit(1)

    df = pd.read_excel(sys.argv[1], engine='odf')
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    inserted = 0
    updated  = 0
    skipped  = 0

    for _, row in df.iterrows():
        name = str(row.get('Name', '')).strip()
        if not name or name == 'nan':
            skipped += 1
            continue

        weapon_type = TYPE_MAP.get(str(row.get('Type', '')).strip(),
                                   str(row.get('Type', '')).strip())
        is_soul, soul_series = detect_soul(name)

        cur.execute("SELECT id FROM weapons WHERE name = %s", (name,))
        exists = cur.fetchone()

        params = (
            weapon_type,
            parse_int(row.get('Level')),
            parse_int(row.get('PATK')),
            parse_int(row.get('EATK')),
            parse_int(row.get('PDEF')),
            parse_int(row.get('EDEF')),
            parse_int(row.get('SPD')),
            parse_int(row.get('CRIT')),
            parse_int(row.get('HP')),
            parse_int(row.get('SP')),
            str(row.get('Special Effects', '') or '').strip(),
            is_soul,
            soul_series,
        )

        if exists:
            cur.execute("""
                UPDATE weapons SET
                    weapon_type=%, level_req=%s, p_atk=%s, e_atk=%s,
                    p_def=%s, e_def=%s, spd=%s, crit=%s, hp=%s, sp=%s,
                    extra=%s, is_soul_weapon=%s, soul_series=%s
                WHERE name=%s
            """, params + (name,))
            updated += 1
        else:
            cur.execute("""
                INSERT INTO weapons
                    (name, weapon_type, level_req, p_atk, e_atk,
                     p_def, e_def, spd, crit, hp, sp,
                     extra, is_soul_weapon, soul_series)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (name,) + params)
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"✓ Insertados: {inserted}")
    print(f"↺ Actualizados: {updated}")
    print(f"✗ Saltados: {skipped}")

if __name__ == '__main__':
    main()