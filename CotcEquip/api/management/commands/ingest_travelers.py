import csv
import os
from django.core.management.base import BaseCommand
from api.models import Traveler

class Command(BaseCommand):
    help = 'Ingesta de viajeros desde CSV (Soporta BOM y Emojis)'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Ruta al archivo CSV')

    def handle(self, *args, **options):
        file_path = options['csv_file']

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"Archivo no encontrado: {file_path}"))
            return

        created_count = 0
        updated_count = 0

        try:
            # utf-8-sig elimina el molesto \ufeff (BOM)
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Limpiar espacios en blanco de las llaves (columnas)
                    row = {k.strip(): v for k, v in row.items() if k}
                    
                    # Obtener nombre (prioridad a Name, luego Character)
                    name = row.get('Name') or row.get('Character')
                    
                    if not name:
                        continue

                    # Lógica para la rareza basada en tus emojis ⭐️
                    # Si el campo 'Class' tiene 5 estrellas, rarity = 5
                    class_data = row.get('Class', '')
                    rarity = class_data.count('⭐') or class_data.count('⭐️') or 5

                    traveler, created = Traveler.objects.update_or_create(
                        name=name.strip(),
                        defaults={
                            'rarity': rarity,
                            'job': row.get('Job', 'Unknown').strip(),
                            'element': row.get('Element', 'None').strip(),
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"Éxito: {created_count} creados, {updated_count} actualizados."
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))