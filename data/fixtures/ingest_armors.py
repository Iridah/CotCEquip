#!/usr/bin/env python3
"""
ingest_armors.py - Importa armaduras desde armor.json al esquema PostgreSQL.
"""

import re
import sys
from pathlib import Path

from ingest_common import get_connection, parse_stat, clean_text


DEBUG = True


def dbg(*args):
    if DEBUG:
        print("[DEBUG]", *args)


def detect_armor_type(name: str) -> str:
    name_l = name.lower()
    for token in [
        "bandana", "hood", "cap", "hat", "helm",
        "robe", "vest", "armor", "mail", "chainmail",
        "coat", "garb", "garment", "knitwear", "kimono"
    ]:
        if token in name_l:
            return token.title()
    return "Other"


def normalize_text(raw_text: str) -> str:
    text = raw_text.replace("\r", "")
    text = text.replace("\n", "\n")
    text = re.sub(r"\t", "    ", text)
    return text


def parse_block_fields(block: str) -> dict | None:
    fields = {}
    patterns = {
        "item_id": r"ItemID\s*=\s*(\d+)",
        "level": r"Level\s*=\s*(\d+)",
        "hp": r"Max_HP\s*=\s*\"([^\"]*)\"",
        "sp": r"Max_SP\s*=\s*\"([^\"]*)\"",
        "p_atk": r"Phys_Atk\s*=\s*\"([^\"]*)\"",
        "e_atk": r"Elem_Atk\s*=\s*\"([^\"]*)\"",
        "p_def": r"Phys_Def\s*=\s*\"([^\"]*)\"",
        "e_def": r"Elem_Def\s*=\s*\"([^\"]*)\"",
        "spd": r"Speed\s*=\s*\"([^\"]*)\"",
        "crit": r"Critical\s*=\s*\"([^\"]*)\"",
        "extra": r"Extra\s*=\s*\"([^\"]*)\"",
        "buy_value": r"Buy_Value\s*=\s*(\d+)",
        "req_mat": r"Req_Mat\s*=\s*\"([^\"]*)\"",
        "sell_value": r"Sell_Value\s*=\s*(\d+)",
        "link": r"Link\s*=\s*\"([^\"]*)\"",
    }

    for key, pattern in patterns.items():
        m = re.search(pattern, block)
        if not m:
            return None
        fields[key] = m.group(1)

    return fields


def split_groups(text: str):
    group_pattern = re.compile(r'\["(?P<group>Headgear|Body Armor)"\]\s*=\s*\{', re.MULTILINE)
    matches = list(group_pattern.finditer(text))
    groups = []

    for idx, match in enumerate(matches):
        group = match.group("group")
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        groups.append((group, text[start:end]))

    return groups


def split_entries(group_text: str):
    entry_pattern = re.compile(r'\["(?P<name>[^"]+)"\]\s*=\s*\{', re.MULTILINE)
    matches = list(entry_pattern.finditer(group_text))
    entries = []

    for idx, match in enumerate(matches):
        name = match.group("name")
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(group_text)
        entries.append((name, group_text[start:end]))

    return entries


def extract_items(raw_text: str):
    text = normalize_text(raw_text)
    if text.lstrip().startswith("return {"):
        text = text.lstrip()[len("return {"):].strip()

    dbg("texto inicial", text[:300])

    items = []

    for group_name, group_text in split_groups(text):
        dbg("grupo detectado:", group_name)
        entries = split_entries(group_text)
        dbg("entradas en grupo", group_name, len(entries))

        for entry_name, entry_block in entries:
            fields = parse_block_fields(entry_block)
            if not fields:
                dbg("bloque sin match:", entry_name)
                continue

            item = {
                "name": entry_name.strip(),
                "armor_group": group_name,
                "armor_type": detect_armor_type(entry_name),
                "p_def": parse_stat(fields["p_def"]),
                "e_def": parse_stat(fields["e_def"]),
                "p_atk": parse_stat(fields["p_atk"]),
                "e_atk": parse_stat(fields["e_atk"]),
                "spd": parse_stat(fields["spd"]),
                "crit": parse_stat(fields["crit"]),
                "hp": parse_stat(fields["hp"]),
                "sp": parse_stat(fields["sp"]),
                "extra": clean_text(fields["extra"]),
            }
            items.append(item)

    return items

def dedupe_items(items):
    deduped = []
    seen = set()

    for item in items:
        key = (item["armor_group"].strip().lower(), item["name"].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def insert_armors(items):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("TRUNCATE TABLE armors RESTART IDENTITY;")
        sql = """
            INSERT INTO armors (
                name, armor_group, armor_type,
                p_def, e_def, p_atk, e_atk,
                spd, crit, hp, sp, extra
            )
            VALUES (
                %(name)s, %(armor_group)s, %(armor_type)s,
                %(p_def)s, %(e_def)s, %(p_atk)s, %(e_atk)s,
                %(spd)s, %(crit)s, %(hp)s, %(sp)s, %(extra)s
            );
        """
        cur.executemany(sql, items)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 ingest_armors.py Sources/armor.json")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"No se encontró el archivo: {input_file}")
        sys.exit(1)

    raw_text = input_file.read_text(encoding="utf-8", errors="ignore")
    items = extract_items(raw_text)
    #inserto temporal

    from collections import Counter

    name_counts = Counter(item["name"].strip().lower() for item in items)
    duplicates = [name for name, count in name_counts.items() if count > 1]

    print("Nombres duplicados:", len(duplicates))
    for name in duplicates[:20]:
        print("-", name)

#fin inserto temporal
    items = dedupe_items(items)

    print(f"Armors detectadas: {len(items)}")
    print("Muestra de registros:")
    for item in items[:15]:
        print(item)

    if not items:
        print("No se encontraron registros para importar.")
        sys.exit(1)

    # Descomenta cuando verifiques que la muestra es correcta.
    # insert_armors(items)
    # print("Importación de armors completada.")


if __name__ == "__main__":
    main()