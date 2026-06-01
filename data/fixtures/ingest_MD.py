#!/usr/bin/env python3
"""
ingest_travelers_md.py - Extrae trust accessories y skills desde MD de Notion
Uso:
    python ingest_travelers_md.py data/md/          # procesa toda la carpeta
    python ingest_travelers_md.py data/md/Temenos.md # procesa un solo archivo
    --dry-run : imprime sin escribir en BD
"""
import re
import sys
import unicodedata
from pathlib import Path
 
from ingest_common import get_connection, clean_text
 
# ── Normalización de nombres ─────────────────────────────────────────────────
 
CHAR_MAP = {
    'тАЩ': '’', 'тАЬ': '"', 'тАЭ': '"',
    '├й': 'é', '├и': 'è', '├╝': 'ü',
    '├░': 'ð', '├Ж': 'Æ',
}
 
NAME_OVERRIDES = {
    'O Odio': 'O. Odio',
    'S Odio': 'S. Odio',
}
 
EXCLUDE_NAMES = {'3 Stars', '4 Stars', '5 Stars'}
 
def normalize_name(raw: str) -> str:
    name = raw
    for bad, good in CHAR_MAP.items():
        name = name.replace(bad, good)
    name = unicodedata.normalize('NFC', name)
    name = name.strip()
    return NAME_OVERRIDES.get(name, name)
 
# ── Parser de sección A4 ─────────────────────────────────────────────────────
 
STAT_KEYS = {
    'P.Atk': 'p_atk', 'E.Atk': 'e_atk',
    'P.Def': 'p_def', 'E.Def': 'e_def',
    'Spd': 'spd', 'Crit': 'crit',
    'HP': 'hp', 'SP': 'sp',
}
 
def parse_stat_line(line: str) -> dict:
    stats = {}
    pattern = re.compile(r'([+-]?\d+)\s*(P\.Atk|E\.Atk|P\.Def|E\.Def|Spd|Crit|HP|SP)')
    for m in pattern.finditer(line):
        val, key = int(m.group(1)), m.group(2)
        if key in STAT_KEYS:
            stats[STAT_KEYS[key]] = val
    return stats
 
def parse_a4_section(text: str) -> dict | None:
    m = re.search(
        r'## Awakening IV Accessory\s*\n(.*?)(?=\n## |\Z)',
        text, re.DOTALL
    )
    if not m:
        return None
 
    block = m.group(1)
 
    name_m = re.search(r'\*\*"?([^"*\n]+)"?\*\*', block)
    if not name_m:
        return None
    acc_name = name_m.group(1).strip()
 
    stats = {}
    extra_lines = []
    for line in block.splitlines():
        line = line.strip().lstrip('·').strip()
        if not line or line.startswith('<') or line.startswith('!'):
            continue
        parsed = parse_stat_line(line)
        if parsed:
            stats.update(parsed)
        elif line and not line.startswith('**') and not line.startswith('['):
            extra_lines.append(line)
 
    extra = '\n'.join(extra_lines).strip()
 
    return {
        'name':  acc_name,
        'stats': stats,
        'extra': extra,
    }
 
# ── Parser de skills ─────────────────────────────────────────────────────────
 
SKILL_SECTIONS = {
    'passive':   '## Passive Skills',
    'battle':    '## Battle Skills',
    'ultimate':  '## Ultimate Technique',
    'ex':        '## EX skill',
}
 
def clean_skill_text(text: str) -> str:
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'notion://\S+', '', text)
    text = re.sub(r'attachment:\S+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'width="\d+px"', '', text)
    # Limpiar links de Notion: ([✦](https://...)) → (✦)
    text = re.sub(r'\(\[([^\]]+)\]\([^)]+\)\)', r'(\1)', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\[\s*\]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()
 
def extract_skill_name(line: str) -> str:
    # Limpiar links de Notion del nombre: ([✦](https://...)) → (✦)
    line = re.sub(r'\(\[([^\]]+)\]\([^)]+\)\)', r'(\1)', line)
    m = re.search(r'\*\*([^*]+)\*\*', line)
    if m:
        name = m.group(1).strip()
        # Quitar rarity/version tags: (1★), (6★), (✦), (EX), (Initial), Lv.2
        name = re.sub(r'\s*\([^)]*[★✦]\s*[^)]*\)\s*$', '', name)
        name = re.sub(r'\s*\((EX|Initial)\)\s*$', '', name)
        name = re.sub(r'\s*Lv\.\d+\s*$', '', name)
        name = name.strip()
        return name
    return ''
 
def parse_skills(text: str) -> list[dict]:
    skills = []
 
    # Encontrar posiciones de cada sección
    positions = []
    for skill_type, header in SKILL_SECTIONS.items():
        idx = text.find(header)
        if idx != -1:
            positions.append((idx, skill_type, header))
    positions.sort()
 
    # Deduplicar por nombre dentro de cada sección (quedarse con última versión)
    seen_names = {}  # name -> index en skills
 
    for i, (pos, skill_type, header) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        section_text = text[pos:end]
 
        lines = section_text.splitlines()
        current_name = ''
        current_desc = []
 
        def flush():
            nonlocal current_name, current_desc
            if current_name and current_desc:
                desc = clean_skill_text('\n'.join(current_desc))
                if desc:
                    key = (skill_type, current_name)
                    entry = {
                        'skill_type':   skill_type,
                        'name':         current_name,
                        'description':  desc,
                    }
                    if key in seen_names:
                        # Reemplazar con versión más reciente (más alta en rarity)
                        skills[seen_names[key]] = entry
                    else:
                        seen_names[key] = len(skills)
                        skills.append(entry)
            current_name = ''
            current_desc = []
 
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('---'):
                flush()
                continue
 
            is_skill_line = (
                '<img' in line and '**' in line and
                any(t in line for t in ['★', '(Initial)', '(EX)', '(✦)', 'Lv.2',
                                        r'pvs=21))'])
            )
            is_sp_saver = bool(re.match(r'\*\*Lv\.\d+', line))
 
            if is_skill_line and not is_sp_saver:
                flush()
                name = extract_skill_name(line)
                if name:
                    current_name = name
                    current_desc = [line]
            elif current_name and not is_sp_saver:
                current_desc.append(line)
 
        flush()
 
    return skills
 
# ── Procesamiento de un MD ───────────────────────────────────────────────────
 
def process_md(filepath: Path) -> dict | None:
    stem = filepath.stem
    traveler_name = normalize_name(stem)
 
    if traveler_name in EXCLUDE_NAMES:
        return None
 
    text = filepath.read_text(encoding='utf-8', errors='replace')
 
    a4     = parse_a4_section(text)
    skills = parse_skills(text)
 
    return {
        'traveler_name': traveler_name,
        'a4':            a4,
        'skills':        skills,
    }
 
# ── DB ───────────────────────────────────────────────────────────────────────
 
def find_traveler_id(cur, name: str) -> int | None:
    cur.execute("SELECT id FROM travelers_master WHERE name = %s", (name,))
    row = cur.fetchone()
    return row[0] if row else None
 
def upsert_a4(cur, traveler_id: int, a4: dict):
    s = a4['stats']
    cur.execute("""
        UPDATE travelers_master SET
            trust_acc_name  = %s,
            trust_acc_p_atk = %s, trust_acc_e_atk = %s,
            trust_acc_p_def = %s, trust_acc_e_def = %s,
            trust_acc_spd   = %s, trust_acc_crit  = %s,
            trust_acc_hp    = %s, trust_acc_sp    = %s,
            trust_acc_extra = %s
        WHERE id = %s
    """, (
        a4['name'],
        s.get('p_atk', 0), s.get('e_atk', 0),
        s.get('p_def', 0), s.get('e_def', 0),
        s.get('spd', 0),   s.get('crit', 0),
        s.get('hp', 0),    s.get('sp', 0),
        a4['extra'],
        traveler_id,
    ))
 
def upsert_skills(cur, traveler_id: int, skills: list):
    cur.execute("DELETE FROM traveler_skills WHERE traveler_id = %s", (traveler_id,))
    for s in skills:
        cur.execute("""
            INSERT INTO traveler_skills (traveler_id, skill_type, name, description)
            VALUES (%s, %s, %s, %s)
        """, (traveler_id, s['skill_type'], s['name'], s['description']))
 
# ── Main ─────────────────────────────────────────────────────────────────────
 
def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    paths_args = [a for a in args if not a.startswith('--')]
 
    if not paths_args:
        print("Uso: python ingest_travelers_md.py <carpeta_o_archivo> [--dry-run]")
        sys.exit(1)
 
    target = Path(paths_args[0])
    if target.is_dir():
        files = sorted(target.glob('*.md'))
    else:
        files = [target]
 
    conn = None if dry_run else get_connection()
    cur  = None if dry_run else conn.cursor()
 
    ok = skipped = errors = no_match = 0
 
    for f in files:
        try:
            data = process_md(f)
            if data is None:
                skipped += 1
                continue
 
            name   = data['traveler_name']
            a4     = data['a4']
            skills = data['skills']
 
            if dry_run:
                print(f"\n{'='*60}")
                print(f"TRAVELER: {name}")
                if a4:
                    print(f"  A4: {a4['name']}")
                    print(f"  Stats: {a4['stats']}")
                    if a4['extra']:
                        print(f"  Extra: {a4['extra'][:80]}...")
                else:
                    print(f"  A4: (no encontrado)")
                print(f"  Skills: {len(skills)}")
                for s in skills:
                    print(f"    [{s['skill_type']}] {s['name']}")
            else:
                tid = find_traveler_id(cur, name)
                if not tid:
                    print(f"  ✗ Sin match BD: {name}")
                    no_match += 1
                    continue
                if a4:
                    upsert_a4(cur, tid, a4)
                upsert_skills(cur, tid, skills)
 
            ok += 1
 
        except Exception as e:
            print(f"  ERROR en {f.name}: {e}")
            errors += 1
 
    if not dry_run and conn:
        conn.commit()
        cur.close()
        conn.close()
 
    print(f"\n{'DRY RUN - ' if dry_run else ''}Procesados: {ok} | Saltados: {skipped} | Sin match BD: {no_match} | Errores: {errors}")
 
if __name__ == '__main__':
    main()