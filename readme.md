# CotC Equip - Roster & Equipment Manager

Gestor de personajes y equipamiento para **Octopath Traveler: Champions of the Continent**.
Permite visualizar el roster completo y gestionar el estado de reclutamiento de cada viajero.

## Stack

- **Backend:** Python 3.14 / Django 6.0 / Django REST Framework
- **Base de Datos:** PostgreSQL
- **Frontend:** Tailwind CSS (en desarrollo)

## Estado actual

- API REST funcional (`/api/travelers/`)
- Modelo separado: catálogo de personajes (solo lectura) + roster del usuario (editable)
- Grabación a PostgreSQL operativa

## Instalación
```bash
git clone git@github.com:Iridah/CotCEquip.git
cd CotCEquip
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

Configurar `.env` basado en `.env.example`:
```
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=cotc_db
DB_USER=cotc_user
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
```
```bash
cd CotcEquip
python manage.py migrate
python manage.py runserver
```

## Endpoints disponibles

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/travelers/` | Lista todos los viajeros |
| GET | `/api/travelers/{id}/` | Detalle de un viajero |
| POST | `/api/travelers/{id}/roster/` | Crear/actualizar estado del roster |