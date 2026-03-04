# Importamos el modelo desde el archivo físico travelers.py
from .travelers import Traveler, RosterEntry
from .weapons import Weapon
from .armors import Armor
from .accessories import Accessory
from .pets import Pet

# Esto permite que otras partes de la app (como tus comandos)
# puedan hacer "from api.models import Traveler" directamente.