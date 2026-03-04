"""
ingest_travelers.py (version unificada)
Uso: python ingest_travelers.py <ruta_al_csv>
"""

import csv, os, re, sys
from urllib.parse import unquote

DB_CONFIG = {
    'dbname':   'cotc_db',
    'user':     'cotc_user',
    'password': 'ShWRmx6eBmPubZve7GKidkjPeMbd9fUv3iHe',
    'host':     '127.0.0.1',
    'port':     5432,
}

WEAPON_MAP = {
    'Sword': 'Sword', 'Dagger': 'Dagger', 'Axe': 'Axe', 'Bow': 'Bow',
    'Staff': 'Staff', 'Staff_Staves': 'Staff',
    'Spear_Polearm': 'Polearm', 'Polearm': 'Polearm',
    'Fan': 'Fan', 'Tome': 'Tome',
}

ELEMENT_MAP = {
    'Fire': 'Fire', 'Ice': 'Ice', 'Lightning': 'Lightning',
    'Lightning_Thunder': 'Lightning', 'Wind': 'Wind',
    'Light': 'Light', 'Dark': 'Dark',
}

JOB_WEAPON_FALLBACK = {
    'Warrior': 'Sword', 'Thief': 'Dagger', 'Cleric': 'Staff',
    'Scholar': 'Tome', 'Merchant': 'Polearm', 'Dancer': 'Fan',
    'Apothecary': 'Axe', 'Hunter': 'Bow',
}

def parse_attributes(attrs_raw):
    decoded = unquote(attrs_raw)
    files = re.findall(r'/([^/]+)\.png', decoded)
    weapons, elements = [], []
    for fname in files:
        clean = re.sub(r'\s*\d+$', '', fname).strip()
        if clean in WEAPON_MAP:
            weapons.append(WEAPON_MAP[clean])
        elif clean in ELEMENT_MAP:
            elements.append(ELEMENT_MAP[clean])
    return (
        weapons[0] if weapons else None,
        elements[0] if elements else 'None',
        ', '.join(dict.fromkeys(weapons))
    )

def parse_rarity(class_str):
    count = class_str.count('⭐')
    return count if count > 0 else 5

def safe_int(val, default=0):
    try:
        return int(str(val).replace(',', '').strip())
    except:
        return default

def main():
    if len(sys.argv) < 2:
        print("Uso: python ingest_travelers.py <ruta_al_csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"Error: archivo no encontrado: {csv_path}")
        sys.exit(1)

    import psycopg2
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Asegurar columnas nuevas
    cur.execute("""
        ALTER TABLE travelers_master
            ADD COLUMN IF NOT EXISTS weapon_types VARCHAR(100) DEFAULT '';
    """)
    conn.commit()

    inserted = updated = 0

    with open(csv_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items() if k}
            name = row.get('Name', '').strip()
            if not name:
                continue

            job    = row.get('Job', 'Unknown').strip()
            rarity = parse_rarity(row.get('Class', ''))
            weapon_primary, element, weapon_types = parse_attributes(row.get('Attributes', ''))
            if not weapon_primary:
                weapon_primary = JOB_WEAPON_FALLBACK.get(job, 'Unknown')

            # Solo stats _120 que existen en la BD
            hp_120    = safe_int(row.get('HP (Lv. 120)'))
            sp_120    = safe_int(row.get('SP (Lv. 120)'))
            p_atk_120 = safe_int(row.get('P.Atk (Lv. 120)'))
            p_def_120 = safe_int(row.get('P.Def (Lv. 120)'))
            e_atk_120 = safe_int(row.get('E.Atk (Lv. 120)'))
            e_def_120 = safe_int(row.get('E.Def (Lv. 120)'))
            crit_120  = safe_int(row.get('Crit (Lv. 120)'))
            spd_120   = safe_int(row.get('Spd (Lv. 120)'))

            cur.execute("SELECT id FROM travelers_master WHERE name = %s", (name,))
            existing = cur.fetchone()

            if existing:
                cur.execute("""
                    UPDATE travelers_master SET
                        rarity=%s, job=%s, weapon_type=%s, element=%s, weapon_types=%s,
                        hp_120=%s, sp_120=%s, p_atk_120=%s, p_def_120=%s,
                        e_atk_120=%s, e_def_120=%s, crit_120=%s, spd_120=%s
                    WHERE name = %s
                """, (
                    rarity, job, weapon_primary, element, weapon_types,
                    hp_120, sp_120, p_atk_120, p_def_120,
                    e_atk_120, e_def_120, crit_120, spd_120,
                    name
                ))
                updated += 1
            else:
                cur.execute("""
                    INSERT INTO travelers_master (
                        name, rarity, job, weapon_type, element, weapon_types,
                        hp_120, sp_120, p_atk_120, p_def_120,
                        e_atk_120, e_def_120, crit_120, spd_120,
                        is_released, created_at,
                        is_obtained, is_6_stars, awakening_level, ultimate_level,
                        is_ultimate_awakened, has_ultimate_overcharge,
                        bless_hp, bless_sp, bless_p_atk, bless_p_def,
                        bless_e_atk, bless_e_def, bless_crit, bless_spd,
                        p_dps, e_dps, tankiness, healer, buffer,
                        debuffer, breaker, damage_coverage, total_score
                    ) VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        true, NOW(),
                        false,false,0,0,false,false,
                        0,0,0,0,0,0,0,0,
                        'C','C','C','C','C','C','C',0,0.0
                    )
                """, (
                    name, rarity, job, weapon_primary, element, weapon_types,
                    hp_120, sp_120, p_atk_120, p_def_120,
                    e_atk_120, e_def_120, crit_120, spd_120,
                ))
                print(f"  + Nuevo: {name} ({job})")
                inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✓ {inserted} insertados, {updated} actualizados.")

if __name__ == '__main__':
    main()