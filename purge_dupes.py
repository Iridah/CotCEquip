#!/usr/bin/env python3
from pathlib import Path

DUPES_FILE = Path("/home/vstore/Programacion/CotCEquip/dupes.txt")
DRY_RUN = False  # pon False cuando ya estés seguro

base_prefix = "homevstoreProgramacionCotCEquipstaticrawimages"
real_base = "/home/vstore/Programacion/CotCEquip/static/raw_images"

to_delete = []

with DUPES_FILE.open(encoding="utf-8") as f:
    current_group = []
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith("--- Grupo ---"):
            if len(current_group) > 1:
                # conservar el primero, borrar el resto
                to_delete.extend(current_group[1:])
            current_group = []
        else:
            current_group.append(line)

    # último grupo si no termina en '--- Grupo ---'
    if len(current_group) > 1:
        to_delete.extend(current_group[1:])

# normalizar rutas a absolutas reales
paths = []
for raw in to_delete:
    # transformar homevstoreProgramacion... -> /home/vstore/Programacion...
    # según el formato que genera tu script
    fixed = raw.replace(base_prefix, real_base)
    p = Path("/" + fixed) if not fixed.startswith("/") else Path(fixed)
    paths.append(p)

print(f"Encontrados {len(paths)} archivos duplicados para borrar.")

for p in paths:
    if not p.exists():
        print(f"[NO EXISTE] {p}")
        continue
    if DRY_RUN:
        print(f"[DRY-RUN] borrar {p}")
    else:
        print(f"[BORRANDO] {p}")
        p.unlink()
