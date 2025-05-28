from django.db import models


# Model to represent a phone device
class Phone(models.Model):
    phone_id = models.CharField(max_length=255, unique=True)  # Unique identifier for the phone
    model = models.CharField(max_length=255)  # Model name or number of the phone
    battery_level = models.IntegerField()  # Current battery level
    lat = models.FloatField()  # Latest known latitude
    lon = models.FloatField()  # Latest known longitude
    timestamp = models.DateTimeField(auto_now=True)  # Last updated time (auto-updated on save)
    is_active = models.BooleanField(default=False)  # Whether the phone is considered active

    def __str__(self):
        return self.phone_id  # Human-readable representation


# Model to store location tracking data related to a phone
class PhoneTrack(models.Model):
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='tracks')  # Link to the phone
    lat = models.FloatField()  # Latitude at the time of tracking
    lon = models.FloatField()  # Longitude at the time of tracking
    speed = models.FloatField(blank=True, null=True)  # Optional speed value
    model = models.CharField(max_length=255, blank=True, null=True)  # Optional phone model info
    battery = models.IntegerField(blank=True, null=True)  # Optional battery level
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)  # Time of tracking (indexed for performance)
    session_id = models.CharField(max_length=100, null=True, blank=True)  # Optional session identifier

    def __str__(self):
        # Human-readable format combining phone ID and timestamp
        return f"{self.phone.phone_id} @ {self.timestamp.strftime('%H:%M:%S')}"
