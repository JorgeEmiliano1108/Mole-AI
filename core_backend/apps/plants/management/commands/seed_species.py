# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================

from django.core.management.base import BaseCommand
from apps.plants.models import SpeciesCatalog


class Command(BaseCommand):
    help = 'Seed the SpeciesCatalog with endemic and native Mexican flora data.'

    def handle(self, *args, **options):
        species_data = [
            {
                "scientific_name": "Agave tequilana",
                "common_name": "Agave azul",
                "ideal_humidity_min": 40.0,
                "ideal_humidity_max": 60.0,
                "ideal_temp_min": 15.0,
                "ideal_temp_max": 35.0,
                "ideal_ph_min": 6.0,
                "ideal_ph_max": 7.5,
                "ideal_ph_optimal": 6.8,
                "description": "Especie endémica de Jalisco y zonas áridas de México. Base para producción de tequina. Requiere suelos bien drenados, alta exposición solar y riego controlado en etapas tempranas.",
                "habitat": "Zonas semiáridas de Jalisco, 1500-2000 m.s.n.m.",
                "soil_type": "Suelos bien drenados, arena‑arcilla.",
                "irrigation": "Riego moderado en fase vegetativa, escaso en maduración.",
                "uses": "Producción de tequila, fibra, ornamental.",
                "uv_rays": 5.0,
                "soil_humidity_min": 15.0,
                "soil_humidity_max": 30.0,
                "is_protected_nom059": False,
                "protection_category": "",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/Agave_tequilana.jpg/640px-Agave_tequilana.jpg"
            },
            {
                "scientific_name": "Opuntia ficus-indica",
                "common_name": "Nopal",
                "ideal_humidity_min": 30.0,
                "ideal_humidity_max": 50.0,
                "ideal_temp_min": 10.0,
                "ideal_temp_max": 40.0,
                "ideal_ph_min": 6.5,
                "ideal_ph_max": 8.0,
                "ideal_ph_optimal": 7.2,
                "description": "Cactácea endémica de México, adaptada a climas áridos y semiáridos. Alto valor nutricional (vitaminas A, C, calcio). Tolerante a sequías prolongadas y suelos pobres.",
                "habitat": "Zonas áridas y semiáridas de México, a nivel de altitud media.",
                "soil_type": "Suelos pobres, bien drenados, arena‑arcilla.",
                "irrigation": "Escasa, solo riego puntual en períodos secos.",
                "uses": "Alimentación, forraje, uso ornamental.",
                "uv_rays": 6.0,
                "soil_humidity_min": 10.0,
                "soil_humidity_max": 25.0,
                "is_protected_nom059": False,
                "protection_category": "",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/Opuntia_ficus-indica.jpg/640px-Opuntia_ficus-indica.jpg"
            },
            {
                "scientific_name": "Tagetes erecta",
                "common_name": "Cempasúchil",
                "ideal_humidity_min": 50.0,
                "ideal_humidity_max": 70.0,
                "ideal_temp_min": 15.0,
                "ideal_temp_max": 25.0,
                "ideal_ph_min": 6.0,
                "ideal_ph_max": 7.5,
                "ideal_ph_optimal": 6.5,
                "description": "Planta herbácea nativa de México, icónica en la celebración de Día de Muertos. Requiere suelos ricos en materia orgánica, riego regular y protección de heladas.",
                "habitat": "Campos y jardines de altitud baja a media en México.",
                "soil_type": "Suelos ricos en materia orgánica, franco‑arenosos.",
                "irrigation": "Riego regular, evitar encharcamiento.",
                "uses": "Decoración, tradición cultural, extractos aromáticos.",
                "uv_rays": 5.5,
                "soil_humidity_min": 30.0,
                "soil_humidity_max": 45.0,
                "is_protected_nom059": False,
                "protection_category": "",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/Tagetes_erecta.jpg/640px-Tagetes_erecta.jpg"
            },
            {
                "scientific_name": "Zea mays raza Palomero Toluqueño",
                "common_name": "Maíz Palomero",
                "ideal_humidity_min": 50.0,
                "ideal_humidity_max": 75.0,
                "ideal_temp_min": 12.0,
                "ideal_temp_max": 24.0,
                "ideal_ph_min": 5.5,
                "ideal_ph_max": 7.0,
                "ideal_ph_optimal": 6.0,
                "description": "Raza de maíz nativa del Valle de Toluca, adaptada a altitudes elevadas (2,600-3,000 msnm). Grano pequeño y duro para elaboración de palomitas. Sensible a sequía y requiere suelos profundos.",
                "habitat": "Valle de Toluca, altitudes de 2,600‑3,000 m.",
                "soil_type": "Suelos profundos, bien drenados, con materia orgánica.",
                "irrigation": "Riego moderado, evitar déficit hídrico.",
                "uses": "Alimentación humana, palomitas, forraje.",
                "uv_rays": 5.0,
                "soil_humidity_min": 20.0,
                "soil_humidity_max": 35.0,
                "is_protected_nom059": True,
                "protection_category": "Pr",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/Zea_mays.jpg/640px-Zea_mays.jpg"
            },
            {
                "scientific_name": "Echinocactus platyacanthus",
                "common_name": "Biznaga Barril",
                "ideal_humidity_min": 20.0,
                "ideal_humidity_max": 40.0,
                "ideal_temp_min": 5.0,
                "ideal_temp_max": 35.0,
                "ideal_ph_min": 6.5,
                "ideal_ph_max": 8.5,
                "ideal_ph_optimal": 7.5,
                "description": "Cactácea endémica de los desiertos de San Luis Potosí y Zacatecas. Su hábitat se ve amenazado por extracción ilegal como planta ornamental. Crece en suelos calizos, alta exposición solar y nula humedad ambiental.",
                "habitat": "Desiertos de San Luis Potosí y Zacatecas, altitudes bajas.",
                "soil_type": "Suelos calizos, bien drenados.",
                "irrigation": "Casi nula, tolera sequía extrema.",
                "uses": "Ornamental, medicinal tradicional.",
                "uv_rays": 7.0,
                "soil_humidity_min": 5.0,
                "soil_humidity_max": 15.0,
                "is_protected_nom059": True,
                "protection_category": "Pr",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/Echinocactus_platyacanthus.jpg/640px-Echinocactus_platyacanthus.jpg"
            }
        ]

        created_count = 0
        updated_count = 0

        for species in species_data:
            try:
                obj, created = SpeciesCatalog.objects.update_or_create(
                    scientific_name=species["scientific_name"],
                    defaults=species
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"[OK] Created: {species['scientific_name']}"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"[UPDATED] {species['scientific_name']}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[ERROR] {species['scientific_name']}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"\nSummary: {created_count} created, {updated_count} updated."))
