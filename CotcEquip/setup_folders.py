import os
from pathlib import Path

def create_structure():
    # Definimos la raíz del proyecto (donde se ejecuta el script)
    base_path = Path.cwd()

    # Mapa de carpetas a crear
    folders = [
        "api/management/commands",
        "api/migrations",
        "api/templates/api/components",
        "data/fixtures",
        "static/sprites",
        "static/css",
        "static/js",
        "static/raw_images",
        "static/assets",
    ]

    # Archivos base necesarios para que Python reconozca los módulos
    init_files = [
        "api/__init__.py",
        "api/management/__init__.py",
        "api/management/commands/__init__.py",
    ]

    print(f"🚀 Iniciando construcción de arquitectura en: {base_path}\n")

    # 1. Crear Carpetas
    for folder in folders:
        folder_path = base_path / folder
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Carpeta creada: {folder}")
        else:
            print(f"🟡 Ya existe: {folder}")

    # 2. Crear archivos __init__.py faltantes
    for init_file in init_files:
        file_path = base_path / init_file
        if not file_path.exists():
            file_path.touch()
            print(f"📝 Archivo creado: {init_file}")

    # 3. Crear archivos placeholder para evitar errores de importación inicial
    placeholders = {
        "api/urls.py": "from django.urls import path\n\nurlpatterns = []",
        "api/serializers.py": "from rest_framework import serializers",
    }

    for path_str, content in placeholders.items():
        file_path = base_path / path_str
        if not file_path.exists():
            with open(file_path, "w") as f:
                f.write(content)
            print(f"📄 Archivo base creado: {path_str}")

    print("\nEstructura lista. Ahora puedes ejecutar: python manage.py startapp api (si no lo has hecho)")

if __name__ == "__main__":
    create_structure()