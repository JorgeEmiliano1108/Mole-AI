import logging
from django.core.management.base import BaseCommand
from apps.plants.models import SpeciesCatalog

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Seeder de Fichas Técnicas (Cultivos/Plantas) para el Buscador Sigiloso'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE(">> INICIANDO INYECCIÓN DE DATOS DE ESPECIES BOTÁNICAS..."))

        plants_data = [
            {
                "common_name": "Manzanilla",
                "scientific_name": "Matricaria chamomilla",
                "ideal_humidity_min": 60.0,
                "ideal_humidity_max": 70.0,
                "ideal_temp_min": 20.0,
                "ideal_temp_max": 25.0,
                "ideal_ph_min": 6.5,
                "ideal_ph_max": 7.0,
                "description": "Especie catalogada prioritaria. Requiere monitoreo continuo de humedad. Útil para ungüentos medicinales en condiciones de escasez."
            },
            {
                "common_name": "Maíz",
                "scientific_name": "Zea mays",
                "ideal_humidity_min": 50.0,
                "ideal_humidity_max": 75.0,
                "ideal_temp_min": 20.0,
                "ideal_temp_max": 30.0,
                "ideal_ph_min": 5.8,
                "ideal_ph_max": 7.0,
                "description": "Base alimentaria del Búnker Central. Tolerancia media a la radiación secundaria. Vital para la supervivencia a largo plazo."
            },
            {
                "common_name": "Tomate",
                "scientific_name": "Solanum lycopersicum",
                "ideal_humidity_min": 60.0,
                "ideal_humidity_max": 80.0,
                "ideal_temp_min": 21.0,
                "ideal_temp_max": 27.0,
                "ideal_ph_min": 6.0,
                "ideal_ph_max": 6.8,
                "description": "Cultivo hidropónico sensible a necrosis foliar. Aporte vitamínico esencial. Requiere control estricto del pH."
            },
            {
                "common_name": "Frijol",
                "scientific_name": "Phaseolus vulgaris",
                "ideal_humidity_min": 50.0,
                "ideal_humidity_max": 65.0,
                "ideal_temp_min": 18.0,
                "ideal_temp_max": 26.0,
                "ideal_ph_min": 6.0,
                "ideal_ph_max": 7.5,
                "description": "Leguminosa fijadora de nitrógeno. Cultivo táctico para recuperación de suelos degradados por la lluvia ácida."
            },
            {
                "common_name": "Chile Habanero",
                "scientific_name": "Capsicum chinense",
                "ideal_humidity_min": 70.0,
                "ideal_humidity_max": 85.0,
                "ideal_temp_min": 24.0,
                "ideal_temp_max": 32.0,
                "ideal_ph_min": 5.5,
                "ideal_ph_max": 6.5,
                "description": "Especímen de alto rendimiento calórico. Resistencia extrema al estrés térmico. Uso culinario y síntesis química disuasoria."
            }
        ]

        created_count = 0
        updated_count = 0

        for data in plants_data:
            obj, created = SpeciesCatalog.objects.get_or_create(
                scientific_name=data["scientific_name"],
                defaults={
                    "common_name": data["common_name"],
                    "ideal_humidity_min": data["ideal_humidity_min"],
                    "ideal_humidity_max": data["ideal_humidity_max"],
                    "ideal_temp_min": data["ideal_temp_min"],
                    "ideal_temp_max": data["ideal_temp_max"],
                    "ideal_ph_min": data["ideal_ph_min"],
                    "ideal_ph_max": data["ideal_ph_max"],
                    "ideal_ph_optimal": (data["ideal_ph_min"] + data["ideal_ph_max"]) / 2,
                    "description": data["description"]
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"[ADD] >> {obj.common_name} ({obj.scientific_name}) registrado en BD."))
            else:
                updated_count += 1
                # Actualizar si ya existe para asegurar que tenga los datos correctos
                for key, value in data.items():
                    setattr(obj, key, value)
                obj.ideal_ph_optimal = (data["ideal_ph_min"] + data["ideal_ph_max"]) / 2
                obj.save()
                self.stdout.write(self.style.WARNING(f"[UPD] >> {obj.common_name} ({obj.scientific_name}) actualizado."))

        self.stdout.write(self.style.SUCCESS(f">> OPERACIÓN COMPLETADA. Nuevas: {created_count} | Actualizadas: {updated_count}"))
