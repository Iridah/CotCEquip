# Importamos el modelo desde el archivo físico travelers.py
from .travelers import Traveler, RosterEntry

# Esto permite que otras partes de la app (como tus comandos)
# puedan hacer "from api.models import Traveler" directamente.