from rest_framework import serializers
from .models import Phone, PhoneTrack

# Serializer for PhoneTrack model
class PhoneTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneTrack  # The model this serializer is for
        fields = ['lat', 'lon', 'speed', 'timestamp']  # Fields to include in the serialized output

# Serializer for Phone model with nested track data
class PhoneSerializer(serializers.ModelSerializer):
    # Nested serializer to include related PhoneTrack entries
    tracks = PhoneTrackSerializer(many=True, read_only=True)

    class Meta:
        model = Phone  # The model this serializer is for
        fields = ['phone_id', 'model', 'lat', 'lon', 'battery_level', 'timestamp', 'tracks']  # Fields to serialize
