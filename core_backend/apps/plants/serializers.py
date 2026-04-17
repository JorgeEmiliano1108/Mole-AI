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
from rest_framework import serializers



class PlantCreateSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    species_id = serializers.UUIDField(required=False, allow_null=True)


class PlantUpdateSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    species_id = serializers.UUIDField(required=False, allow_null=True)


class PlantResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nickname = serializers.CharField(allow_null=True)
    species_id = serializers.UUIDField(source='species.id', allow_null=True, read_only=True)
    created_at = serializers.DateTimeField()


class FavoritePlantSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.IntegerField(read_only=True)
    plant = serializers.UUIDField()
    created_at = serializers.DateTimeField(read_only=True)


class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        from apps.plants.models import SpeciesCatalog

        model = SpeciesCatalog
        fields = [
            'id',
            'scientific_name',
            'common_name',
            'description',
            'ideal_humidity_min',
            'ideal_humidity_max',
            'ideal_temp_min',
            'ideal_temp_max',
            'ideal_ph_min',
            'ideal_ph_max',
            'ideal_ph_optimal',
            'image_url',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Basic cross-field validation: ensure min <= max when both present
        if data.get('ideal_humidity_min') is not None and data.get('ideal_humidity_max') is not None:
            if data['ideal_humidity_min'] > data['ideal_humidity_max']:
                raise serializers.ValidationError('ideal_humidity_min cannot be greater than ideal_humidity_max')
        if data.get('ideal_temp_min') is not None and data.get('ideal_temp_max') is not None:
            if data['ideal_temp_min'] > data['ideal_temp_max']:
                raise serializers.ValidationError('ideal_temp_min cannot be greater than ideal_temp_max')
        return data

