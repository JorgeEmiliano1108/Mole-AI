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


# class FavoritePlantSerializer
    class Meta:
        # model = FavoritePlant
        fields = ['id', 'user', 'plant', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

