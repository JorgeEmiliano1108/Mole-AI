from rest_framework import serializers


class PlantCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    species = serializers.CharField(max_length=150, required=False, default="")
    location = serializers.CharField(max_length=255, required=False, default="")
    notes = serializers.CharField(required=False, default="")


class PlantUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    species = serializers.CharField(max_length=150, required=False)
    location = serializers.CharField(max_length=255, required=False)
    notes = serializers.CharField(required=False)


class PlantResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    species = serializers.CharField()
    location = serializers.CharField()
    notes = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
