from datetime import timedelta
from django.http import JsonResponse, FileResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Phone, PhoneTrack
from .serializers import PhoneSerializer
from .utils import save_shapefile
import json
import os
import logging
import math

# Logging configuration
logging.basicConfig(level=logging.INFO, filename='./logs/shapefile.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs('./logs', exist_ok=True)


# ViewSet for RESTful APIs
class PhoneViewSet(viewsets.ModelViewSet):
    queryset = Phone.objects.all()  # Get all Phone objects
    serializer_class = PhoneSerializer  # Use PhoneSerializer for serialization

    def create(self, request, *args, **kwargs):
        logger.info("Received create request")  # Log that a create request was received

        # Extract data from the request
        phone_id = request.data.get('phone_id')
        lat = request.data.get('lat')
        lon = request.data.get('lon')
        battery_level = request.data.get('battery_level')

        # Debug log with the received data
        logger.debug(f"Create data: phone_id={phone_id}, lat={lat}, lon={lon}, battery={battery_level}")

        # Check for missing required fields
        if not all([phone_id, lat, lon]):
            logger.error("Missing required fields")
            return Response({"status": "error", "message": "Missing required fields"}, status=400)

        # Create or update the Phone entry
        phone, created = Phone.objects.update_or_create(
            phone_id=phone_id,
            defaults={'lat': lat, 'lon': lon, 'battery_level': battery_level}
        )

        # Log whether the phone was created or updated
        logger.info(f"Phone {'created' if created else 'updated'}: {phone_id}")

        # Return success response
        return Response({"status": "success", "phone_id": phone_id})


# Show map
def map_view(request):
    # Retrieve all phone records from the database
    # phones = Phone.objects.all()
    phones = Phone.objects.filter(is_active=True)
    # Log that the map view is being rendered
    logger.info("Rendering map view")

    # Render the 'map.html' template with the list of phones
    return render(request, 'map.html', {'phones': phones})

#handles the saving of a phone's position, updating or creating a phone record in the database,
# Saving location
@csrf_exempt
def save_position(request):
    # Log the incoming request to save phone position

    logger.info("Received save_position request")
    # Check if the request method is POST, return an error if not

    if request.method != 'POST':
        logger.error("Invalid method")
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=400)

    try:
        # Parse the incoming JSON request data

        data = json.loads(request.body)
        phone_id = data.get('phone_id')
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        speed = data.get('speed')
        model = data.get('model')
        battery = data.get('battery')
        is_active = data.get('is_active', False)
        session_id = data.get('session_id')
        # Check if the required fields are present, return error if any are missing

        if not all([phone_id, lat, lon]):
            logger.error("Invalid or missing required fields")
            return JsonResponse({"status": "error", "message": "Invalid or missing required fields"}, status=400)

        try:
            # Try to find the existing phone by its phone_id

            phone = Phone.objects.get(phone_id=phone_id)
        except Phone.DoesNotExist:
            # If the phone doesn't exist, create a new one with the provided data

            phone = Phone.objects.create(
                phone_id=phone_id,
                lat=lat,
                lon=lon,
                battery_level=battery or 0,
                model=model or "Unknown",
                is_active=is_active
            )
            logger.info(f"Created new phone: {phone_id}")

        # If the phone is deactivated and a session_id is provided, save the track data as shapefile
        if not is_active and session_id and phone.is_active:
            tracks = PhoneTrack.objects.filter(phone=phone, session_id=session_id).order_by('timestamp')
            coords = [(t.lon, t.lat) for t in tracks if t.lon is not None and t.lat is not None]
            if len(coords) >= 2:
                base_name = save_shapefile(coords, phone_id, session_id)
                logger.info(f"Shapefile created on stop: {base_name}")
        # Update the phone object with the latest data

        phone.lat = lat
        phone.lon = lon
        if battery is not None:
            phone.battery_level = battery
        if model is not None:
            phone.model = model
        phone.is_active = is_active
        phone.timestamp = timezone.now()
        phone.save()
        logger.info(f"Updated phone: {phone_id}")

        last_track = PhoneTrack.objects.filter(phone=phone).order_by('-timestamp').first()
        # Create a new PhoneTrack object for the latest position

        PhoneTrack.objects.create(
            phone=phone,
            lat=lat,
            lon=lon,
            speed=speed,
            model=model,
            battery=battery,
            session_id=session_id
        )
        logger.info(f"Created PhoneTrack for phone: {phone_id}")
        # Return a success response
        return JsonResponse({"status": "success", "message": "Data stored successfully"})

    except (ValueError, TypeError):
        # Handle invalid data format error
        logger.error("Invalid data format")
        return JsonResponse({"status": "error", "message": "Invalid data format"}, status=400)
    except Exception as e:
        # Handle any other exceptions and log the error
        logger.error(f"Error in save_position: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# save track as shapefile
@csrf_exempt
def save_track_as_shapefile(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)

    try:
        data = json.loads(request.body)
        phone_id = data.get('phone_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if not all([phone_id, start_time, end_time]):
            return JsonResponse({'status': 'error', 'message': 'Missing phone_id or time range'}, status=400)

        phone = Phone.objects.get(phone_id=phone_id)

        start = timezone.datetime.fromisoformat(start_time)
        end = timezone.datetime.fromisoformat(end_time)

        tracks = PhoneTrack.objects.filter(
            phone=phone,
            timestamp__gte=start,
            timestamp__lte=end
        ).order_by('timestamp')

        coords = [(t.lon, t.lat) for t in tracks if t.lat and t.lon]

        if len(coords) < 2:
            return JsonResponse({'status': 'error', 'message': 'کمتر از ۲ مختصات معتبر یافت شد'}, status=400)

        base_name = save_shapefile(coords, phone_id, phone.model or "unknown")
        return JsonResponse({
            'status': 'success',
            'message': 'Shapefile created',
            'files': {
                'shp': f'/download/{base_name}.shp',
                'shx': f'/download/{base_name}.shx',
                'dbf': f'/download/{base_name}.dbf',
                'prj': f'/download/{base_name}.prj',
            }
        })

    except Exception as e:
        logger.error(f"Error in save_track_shapefile: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



# Downloading file
def download_file(request, filename):
    # Log the file download request
    logger.info(f"Download request for file: {filename}")

    # Construct the file path
    filepath = os.path.join('shapefiles', filename)

    # Check if the file exists
    if os.path.exists(filepath):
        # Log and return the file as an attachment
        logger.info(f"File found, serving: {filepath}")
        return FileResponse(open(filepath, 'rb'), as_attachment=True)

    # Log error and return JSON response if file is not found
    logger.error(f"File not found: {filepath}")
    return JsonResponse({"status": "error", "message": "File not found"}, status=404)


# getting latest phone locations
def get_latest_phones(request):
    # Log that the request was received
    logger.info("Received get_latest_phones request")

    # Get current time
    now = timezone.now()

    # Define a time threshold (30 seconds ago)
    one_minute_ago = now - timedelta(seconds=30)

    # Deactivate phones that haven't updated in the last 30 seconds
    Phone.objects.filter(timestamp__lt=one_minute_ago, is_active=True).update(is_active=False)

    # Retrieve all active phones with selected fields
    phones = Phone.objects.filter(is_active=True).values(
        'phone_id', 'lat', 'lon', 'model', 'battery_level', 'timestamp', 'is_active'
    )

    # Log the number of active phones being returned
    logger.info(f"Returning {len(phones)} active phones")

    # Return the list of active phones as JSON
    return JsonResponse({'phones': list(phones)})



#This function retrieves the latest speed of a phone identified by phone_id by fetching the most recent track entry and returning the speed, or 0 if no track is found or the phone does not exist.
# Getting latest speed of phone
def get_phone_latest(request, phone_id):
    # Log the incoming request with phone_id
    logger.info(f"Received get_phone_latest request for phone_id: {phone_id}")

    try:
        # Try to retrieve the phone object
        phone = Phone.objects.get(phone_id=phone_id)

        # Get the most recent track entry for the phone
        latest_track = PhoneTrack.objects.filter(phone=phone).order_by('-timestamp').first()

        # Log the retrieved speed value
        logger.info(f"Found phone: {phone_id}, latest speed: {latest_track.speed if latest_track else 0}")

        # Return the speed value, 0 if no track is found
        return JsonResponse({
            'speed': latest_track.speed if latest_track else 0,

        })

    except Phone.DoesNotExist:
        # Log if the phone was not found
        logger.error(f"Phone not found: {phone_id}")

        # Return 0 as default speed
        return JsonResponse({'speed': 0})


# This function handles a request to retrieve the tracking data (location history)
# for a specific phone identified by phone_id. It fetches all location records
# (latitude, longitude, timestamp, and session_id) from the database related
# to the specified phone, orders them by timestamp, and returns the data as a
# JSON response. If the phone with the given phone_id does not exist, it returns
# an error message with a 404 status.
def get_phone_tracks(request, phone_id):
    # Log the request for retrieving phone tracks by phone_id

    logger.info(f"Received get_phone_tracks request for phone_id: {phone_id}")

    try:
        phone = Phone.objects.get(phone_id=phone_id)
        tracks = PhoneTrack.objects.filter(phone=phone).order_by('timestamp').values('lat', 'lon', 'timestamp',
                                                                                     'session_id')
        logger.info(f"Returning {len(tracks)} tracks for phone: {phone_id}")
        # Return the list of tracks as a JSON response
        return JsonResponse({'tracks': list(tracks)})
    except Phone.DoesNotExist:
        # Log error if the phone with the given phone_id is not found
        logger.error(f"Phone not found: {phone_id}")
        # Return a JSON response with an error message if the phone is not found
        return JsonResponse({"status": "error", "message": "Phone not found"}, status=404)
