#!/usr/bin/env python3
import hashlib
import os
from pathlib import Path

# CAMBIA ESTA RUTA por la carpeta raíz donde tienes las imágenes "raw"
BASE_DIR = Path("/home/vstore/Programacion/CotCEquip/static/raw_images/")

# extensiones a considerar
EXTS = {".png", ".jpg", ".jpeg", ".webp"}

def file_hash(path: Path, block_size: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            h.update(data)
    return h.hexdigest()

def find_duplicates(base: Path):
    hashes = {}
    duplicates = []  # lista de listas: [original, dup1, dup2...]

    for root, dirs, files in os.walk(base):
        for name in files:
            p = Path(root) / name
            if p.suffix.lower() not in EXTS:
                continue
            h = file_hash(p)
            if h in hashes:
                hashes[h].append(p)
            else:
                hashes[h] = [p]

    for h, paths in hashes.items():
        if len(paths) > 1:
            # paths[0] será el "original", el resto son duplicados
            duplicates.append(paths)

    return duplicates

if __name__ == "__main__":
    dups = find_duplicates(BASE_DIR)
    if not dups:
        print("No se encontraron duplicados.")
    else:
        print("Duplicados encontrados:")
        for group in dups:
            print("\n--- Grupo ---")
            for p in group:
                print(p)
