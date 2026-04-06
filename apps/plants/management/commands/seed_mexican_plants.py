from django.core.management.base import BaseCommand
from apps.plants.models import SpeciesCatalog

class Command(BaseCommand):
    help = 'Seeds the database with native Mexican plant species for RAG and analytical purposes.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Starting evaluation of botanical data...'))

        MEXICAN_PLANTS = [
            {
                "scientific_name": "Agave tequilana",
                "common_name": "Agave Azul",
                "ideal_temp_min": 15.0,
                "ideal_temp_max": 25.0,
                "ideal_humidity_min": 30.0,
                "ideal_humidity_max": 50.0,
                "ideal_ph_min": 6.0,
                "ideal_ph_max": 8.0,
                "ideal_ph_optimal": 7.0,
                "description": "Clima: Árido / Semi-árido.\nTipo de suelo: Franco-arenoso, bien drenado.\nPlagas comunes: Picudo del agave (Scyphophorus acupunctatus), Escama del agave.\nNotas: Especie endémica de México con alta relevancia agroindustrial, principal insumo en la elaboración del tequila."
            },
            {
                "scientific_name": "Opuntia ficus-indica",
                "common_name": "Nopal",
                "ideal_temp_min": 18.0,
                "ideal_temp_max": 28.0,
                "ideal_humidity_min": 20.0,
                "ideal_humidity_max": 40.0,
                "ideal_ph_min": 6.5,
                "ideal_ph_max": 8.5,
                "ideal_ph_optimal": 7.5,
                "description": "Clima: Árido y cálido.\nTipo de suelo: Arenoso o pedregoso, excelente drenaje.\nPlagas comunes: Cochinilla del carmín (Dactylopius coccus), Gusano barrenador del nopal.\nNotas: Cactácea emblemática de México, fundamental en la dieta tradicional y en la iconografía nacional."
            },
            {
                "scientific_name": "Vanilla planifolia",
                "common_name": "Vainilla",
                "ideal_temp_min": 21.0,
                "ideal_temp_max": 32.0,
                "ideal_humidity_min": 70.0,
                "ideal_humidity_max": 90.0,
                "ideal_ph_min": 5.5,
                "ideal_ph_max": 7.0,
                "ideal_ph_optimal": 6.5,
                "description": "Clima: Tropical húmedo.\nTipo de suelo: Rico en materia orgánica, bien drenado (tierra de monte/bosque).\nPlagas comunes: Chinche roja, Pudrición de raíz y tallo (Fusarium spp.).\nNotas: Orquídea trepadora originaria de Mesoamérica, cuyas vainas proveen uno de los aromatizantes más cotizados a nivel global."
            },
            {
                "scientific_name": "Tagetes erecta",
                "common_name": "Cempasúchil",
                "ideal_temp_min": 15.0,
                "ideal_temp_max": 22.0,
                "ideal_humidity_min": 50.0,
                "ideal_humidity_max": 70.0,
                "ideal_ph_min": 6.0,
                "ideal_ph_max": 7.5,
                "ideal_ph_optimal": 6.5,
                "description": "Clima: Templado a cálido.\nTipo de suelo: Fértil y suelto, profundo.\nPlagas comunes: Araña roja, Mosca blanca, Trips.\nNotas: Conocida como la 'flor de muertos', es una especie endémica de profundo valor cultural en México para la festividad de Día de Muertos."
            },
            {
                "scientific_name": "Capsicum annuum",
                "common_name": "Chile Poblano",
                "ideal_temp_min": 18.0,
                "ideal_temp_max": 30.0,
                "ideal_humidity_min": 50.0,
                "ideal_humidity_max": 70.0,
                "ideal_ph_min": 5.5,
                "ideal_ph_max": 6.8,
                "ideal_ph_optimal": 6.2,
                "description": "Clima: Templado cálido.\nTipo de suelo: Franco o franco-arcilloso, buena retención y disponibilidad de nutrientes sin encharcamientos.\nPlagas comunes: Pulgón, Mosca blanca, Minador de la hoja.\nNotas: Variedad de chile inmensamente apreciada en la gastronomía mexicana contemporánea por su sabor y uso en platillos como chiles rellenos y en nogada."
            },
            {
                "scientific_name": "Zea mays everta",
                "common_name": "Maíz Cacahuacintle",
                "ideal_temp_min": 15.0,
                "ideal_temp_max": 24.0,
                "ideal_humidity_min": 50.0,
                "ideal_humidity_max": 75.0,
                "ideal_ph_min": 5.8,
                "ideal_ph_max": 7.0,
                "ideal_ph_optimal": 6.4,
                "description": "Clima: Templado, preferente en zonas de alta montaña o valles altos.\nTipo de suelo: Profundo y con buena materia orgánica disponible.\nPlagas comunes: Gusano cogollero (Spodoptera frugiperda), Gusano elotero, Pulgones.\nNotas: Raza de maíz de grano ancho y harinoso, esencial en las preparaciones festivas como el pozole."
            }
        ]

        created_count = 0
        for plant_data in MEXICAN_PLANTS:
            # Uses get_or_create by scientific_name to ensure idempotency
            scientific_name = plant_data.pop("scientific_name")
            obj, created = SpeciesCatalog.objects.get_or_create(
                scientific_name=scientific_name,
                defaults=plant_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {scientific_name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Skipped (already exists): {scientific_name}"))
        
        self.stdout.write(self.style.SUCCESS(f"Finished seeding! Created {created_count} botanical records."))
