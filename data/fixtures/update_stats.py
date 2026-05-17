#!/usr/bin/env python3
"""
update_stats.py - Actualiza stats Lv.120 en travelers_master desde CSV
Uso: python update_stats.py "Modificacion_stats.csv"
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

# Nombres que difieren entre CSV y BD
NAME_MAP = {
    'Pardis III EX': 'Pardis III EX',   # confirmar nombre exacto en BD
    'Elrica EX2':   'Elrica EX2',       # confirmar
    'Alaune EX2':   'Alaune EX2',       # confirmar
}

def parse_int(val):
    try:
        return int(str(val).replace(',', '').strip())
    except (ValueError, TypeError):
        return None

def main():
    if len(sys.argv) < 2:
        print("Uso: python update_stats.py <archivo.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    updated  = 0
    skipped  = 0
    notfound = []

    with open(csv_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['Name'].strip()
            hp   = parse_int(row.get('HP (Lv. 120)'))

            if not hp:
                print(f"[SKIP] {name} - HP vacío")
                skipped += 1
                continue

            db_name = NAME_MAP.get(name, name)

            cur.execute("SELECT id FROM travelers_master WHERE name = %s", (db_name,))
            result = cur.fetchone()

            if not result:
                notfound.append(name)
                continue

            cur.execute("""
                UPDATE travelers_master SET
                    hp_120   = %s,
                    sp_120   = %s,
                    p_atk_120 = %s,
                    p_def_120 = %s,
                    e_atk_120 = %s,
                    e_def_120 = %s,
                    crit_120  = %s,
                    spd_120   = %s
                WHERE name = %s
            """, (
                hp,
                parse_int(row.get('SP (Lv. 120)')),
                parse_int(row.get('P.Atk (Lv. 120)')),
                parse_int(row.get('P.Def (Lv. 120)')),
                parse_int(row.get('E.Atk (Lv. 120)')),
                parse_int(row.get('E.Def (Lv. 120)')),
                parse_int(row.get('Crit (Lv. 120)')),
                parse_int(row.get('Spd (Lv. 120)')),
                db_name,
            ))
            updated += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✓ Actualizados: {updated}")
    print(f"✗ Saltados (HP vacío): {skipped}")
    if notfound:
        print(f"⚠ No encontrados en BD ({len(notfound)}):")
        for n in notfound:
            print(f"  - {n}")

if __name__ == '__main__':
    main()