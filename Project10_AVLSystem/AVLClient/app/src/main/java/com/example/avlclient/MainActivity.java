package com.example.avlclient;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.drawable.Drawable;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Looper;
import android.preference.PreferenceManager;
import android.provider.Settings;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import org.osmdroid.config.Configuration;
import org.osmdroid.tileprovider.tilesource.TileSourceFactory;
import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.MapView;
import org.osmdroid.views.overlay.Marker;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;
import retrofit2.http.Body;
import retrofit2.http.POST;

// Model class for data being sent to the server
class PositionData {
    public String phone_id;
    public double lat;
    public double lon;
    public float speed;
    public String model;
    public int battery;
    public boolean is_active;
    public String session_id;

    // Constructor for the PositionData class that initializes the position data
// with the provided parameters (phone_id, latitude, longitude, speed, device model, battery level, active status, and session ID)
    public PositionData(String phone_id, double lat, double lon, float speed, String model, int battery, boolean is_active, String session_id) {
        this.phone_id = phone_id;
        this.lat = lat;
        this.lon = lon;
        this.speed = speed;
        this.model = model;
        this.battery = battery;
        this.is_active = is_active;
        this.session_id = session_id;
    }
}

// Model class for the server's response
class ServerResponse {
    public String status;
    public String message;
}

// Interface for defining the API endpoint
interface ApiService {
    @POST("api/save_position/")
    Call<ServerResponse> savePosition(@Body PositionData data);
}

public class MainActivity extends AppCompatActivity {

    private static final int LOCATION_PERMISSION_REQUEST = 1;

    private TextView statusText;
    private MapView map;
    private Marker userMarker;
    private LocationManager locationManager;
    private TextView locationText;
    private TextView phoneIdDisplay;
    private Button startButton;
    private Button stopButton;
    private LinearLayout loadingContainer;
    private ProgressBar locationLoader;
    private TextView locationStatus;
    private String phoneId;
    private Location previousLocation = null;
    private boolean isTracking = false;
    private LocationListener locationListener;
    private ApiService apiService;
    private String sessionId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
// Load configuration settings for the OpenStreetMap (osmdroid) library using the default shared preferences
        Configuration.getInstance().load(getApplicationContext(), PreferenceManager.getDefaultSharedPreferences(getApplicationContext()));
        // Set a custom User-Agent value for the OpenStreetMap (osmdroid) requests, using the app's package name
        Configuration.getInstance().setUserAgentValue(getPackageName());
        // Set the content view of the activity to the layout defined in activity_main.xml
        setContentView(R.layout.activity_main);

        map = findViewById(R.id.mapview);
        locationText = findViewById(R.id.location_text);
        phoneIdDisplay = findViewById(R.id.phone_id_display);
        startButton = findViewById(R.id.startButton);
        stopButton = findViewById(R.id.stopButton);
        statusText = findViewById(R.id.status_text);
        loadingContainer = findViewById(R.id.loading_container);
        locationLoader = findViewById(R.id.location_loader);
        locationStatus = findViewById(R.id.location_status);
        sessionId = null;

        map.setTileSource(TileSourceFactory.MAPNIK);
        map.setBuiltInZoomControls(true);
        map.setMultiTouchControls(true);

        Drawable arrowDrawable = getResources().getDrawable(R.drawable.arrow_marker);
        arrowDrawable.setBounds(0, 0, arrowDrawable.getIntrinsicWidth() * 2, arrowDrawable.getIntrinsicHeight() * 2);

        userMarker = new Marker(map);
        userMarker.setIcon(arrowDrawable);
        userMarker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER);
        userMarker.setTitle("My Location");
        map.getOverlays().add(userMarker);

        map.getController().setZoom(20.0);
        GeoPoint defaultPoint = new GeoPoint(35.6892, 51.3890);
        userMarker.setPosition(defaultPoint);
        map.getController().setCenter(defaultPoint);
        map.invalidate();

        locationManager = (LocationManager) getSystemService(LOCATION_SERVICE);

        phoneId = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
        phoneIdDisplay.setText("Phone ID: " + phoneId);
// Create a new Retrofit instance with a base URL and a Gson converter for handling JSON data
        // Setup Retrofit for making API requests to the server.
// - `baseUrl` defines the root URL of the API.
// - `GsonConverterFactory` is used to convert JSON responses from the server into Java objects.
// Retrofit allows asynchronous communication with the API to save position data.

        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl("http://172.30.23.240:8000/")// Set the base URL for the API (server address)
                .addConverterFactory(GsonConverterFactory.create())// Add GsonConverterFactory to convert JSON responses into Java objects
                .build(); // Build the Retrofit instance
        // Create an implementation of the ApiService interface to interact with the API endpoints
        apiService = retrofit.create(ApiService.class);
// Updates user location on the map, displays coordinates and speed, adjusts map orientation based on movement direction, and optionally sends data to the server if tracking is enabled.
        locationListener = new LocationListener() {
            @Override
            public void onLocationChanged(@NonNull Location location) {
                loadingContainer.setVisibility(View.GONE);

                double lat = location.getLatitude();
                double lon = location.getLongitude();
                float speed = location.getSpeed() * 3.6f;

                locationText.setText("Lat: " + lat + "\nLon: " + lon + "\nSpeed: " + speed + " km/h");

                GeoPoint point = new GeoPoint(lat, lon);
                userMarker.setPosition(point);
                map.getController().setCenter(point);
                // calculate the azimuth from radians to degrees, adjust for positive degrees, and set the map orientation
                if (previousLocation != null) {
                    double lat1 = Math.toRadians(previousLocation.getLatitude());
                    double lon1 = Math.toRadians(previousLocation.getLongitude());
                    double lat2 = Math.toRadians(location.getLatitude());
                    double lon2 = Math.toRadians(location.getLongitude());

                    double dLon = lon2 - lon1;
                    double y = Math.sin(dLon) * Math.cos(lat2);
                    double x = Math.cos(lat1) * Math.sin(lat2) -
                            Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);

                    double azimuthRad = Math.atan2(y, x);
                    float azimuthDeg = (float) ((Math.toDegrees(azimuthRad) + 360) % 360);
                    map.setMapOrientation(-azimuthDeg);
                }

                previousLocation = location;

                if (isTracking) {
                    sendDataToServer(lat, lon, speed);
                }
            }
        };
// Starts location tracking if permission is granted; requests permission otherwise. Shows loading UI, updates status, and begins sending location data.
        startButton.setOnClickListener(v -> {
            if (!isTracking) {
                if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                    ActivityCompat.requestPermissions(this,
                            new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, LOCATION_PERMISSION_REQUEST);
                } else {
                    loadingContainer.setVisibility(View.VISIBLE);
                    statusText.setText("📡 Sending location...");
                    // Generate a unique session ID based on the current time in milliseconds.
// This session ID will be used to associate the location data with a specific tracking session.
// The session ID helps track the status of the user's location updates over time.
                    sessionId = String.valueOf(System.currentTimeMillis());
                    startLocationUpdates();
                    isTracking = true;
                    Toast.makeText(this, "Tracking started", Toast.LENGTH_SHORT).show();
                }
            }
        });

// Stops location tracking, updates the UI, sends final location data to the server, and clears the session ID.
        stopButton.setOnClickListener(v -> {
            if (isTracking) {
                stopLocationUpdates();
                isTracking = false;

                statusText.setText("Tracking stopped");
                new android.os.Handler(Looper.getMainLooper()).postDelayed(() -> statusText.setText(""), 2000);
                locationText.setText("Status 📊📱");
                loadingContainer.setVisibility(View.GONE);

                if (previousLocation != null) {
                    sendDataToServer(previousLocation.getLatitude(), previousLocation.getLongitude(), 0.0f, false, sessionId);
                }
                sessionId = null;
                Toast.makeText(this, "Tracking stopped", Toast.LENGTH_SHORT).show();
            }
        });

        loadingContainer.setVisibility(View.GONE);
        isTracking = false;
    }


    // Start requesting location updates if permission is granted
    private void startLocationUpdates() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED)
            return;
        // Request location updates from the GPS provider with specified parameters:
        // - GPS_PROVIDER: Use GPS to get the location updates
        // - 1000ms: Minimum time interval between location updates (in milliseconds)
        // - 1 meter: Minimum distance change to receive a location update (in meters)
        // - locationListener: A listener that will handle the received location updates
        // - Looper.getMainLooper(): Ensure that location updates are handled on the main th
        locationManager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                1000,
                1,
                locationListener,
                Looper.getMainLooper()
        );
        // If there is a previous location, send it to the server with the current session ID
        if (previousLocation != null) {
            sendDataToServer(previousLocation.getLatitude(), previousLocation.getLongitude(), 0.0f, true, sessionId);
        }
    }
// Stop receiving location updates by removing the location listener
    // Remove the location listener from the LocationManager to stop receiving location updates

    private void stopLocationUpdates() {
        locationManager.removeUpdates(locationListener);
    }

    // Overloaded method to send location data to the server, calling the full version with default parameters
    private void sendDataToServer(double lat, double lon, float speed) {
        // Call the main sendDataToServer method with additional parameters (isActive = true, using current sessionId)
        sendDataToServer(lat, lon, speed, true, sessionId);
    }

    // Sends location and device data to the server
    private void sendDataToServer(double lat, double lon, float speed, boolean isActive, String sessionId) {
        String deviceModel = Build.MODEL;
        BatteryManager bm = (BatteryManager) getSystemService(BATTERY_SERVICE);
        int batteryLevel = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
        // Log the data that is about to be sent to the server for debugging
        Log.d("AVL", "Preparing to send data: lat=" + lat + ", lon=" + lon + ", speed=" + speed + ", is_active=" + isActive + ", session_id=" + sessionId);

        runOnUiThread(() -> statusText.setText("📡 Sending location..."));
        // Create an instance of PositionData, which contains the data to be sent to the server
        PositionData data = new PositionData(phoneId, lat, lon, speed, deviceModel, batteryLevel, isActive, sessionId);
        // Create a call to the server API to save the position data
        Call<ServerResponse> call = apiService.savePosition(data);

        // Make an asynchronous request to the server
        call.enqueue(new Callback<ServerResponse>() {
            // Callback method that handles the server's response to the data being sent
            @Override
            public void onResponse(Call<ServerResponse> call, Response<ServerResponse> response) {
                // Check if the response is successful and contains valid data

                if (response.isSuccessful() && response.body() != null) {
                    ServerResponse serverResponse = response.body();
                    Log.d("AVL", "Success: Status=" + serverResponse.status + ", Message=" + serverResponse.message);
                    // If the server responds with a success status, update the UI with a success message
                    if ("success".equals(serverResponse.status)) {
                        runOnUiThread(() -> statusText.setText("✅ Sent successfully"));
                    } else {
                        // If the server responds with an error message, display it on the UI
                        runOnUiThread(() -> {
                            statusText.setText("⚠️ Error: " + serverResponse.message);
                            new android.os.Handler(Looper.getMainLooper()).postDelayed(() ->
                                    statusText.setText("📡 Sending location..."), 3000);
                        });
                    }
                } else {
                    // If the response is not successful, log the error and update the UI
                    Log.e("AVL", "Error: " + response.code());
                    runOnUiThread(() -> {
                        statusText.setText("⚠️ Error: " + response.code());
                        // Reset the status text to "Sending location..." after 3 seconds
                        new android.os.Handler(Looper.getMainLooper()).postDelayed(() ->
                                statusText.setText("📡 Sending location..."), 3000);
                    });
                }
            }

            // Callback method that handles the failure of the API request (e.g., network error, timeout, etc.)
            @Override
            public void onFailure(Call<ServerResponse> call, Throwable t) {
                // If the request fails, log the error and update the UI to indicate failure
                Log.e("AVL", "Failure: " + t.getMessage());
                // Update the UI to indicate that the data failed to send
                runOnUiThread(() -> {
                    statusText.setText("❌ Failed to send");
                    new android.os.Handler(Looper.getMainLooper()).postDelayed(() ->
                            statusText.setText("📡 Sending location..."), 3000);
                });
            }
        });
    }

    // This method is triggered when the user responds to the location permission request.
// If the permission is granted, location updates are started, and tracking begins.
// If the permission is denied, a message is shown to inform the user that location permission is required.
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == LOCATION_PERMISSION_REQUEST &&
                grantResults.length > 0 &&
                grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            if (isTracking) {
                loadingContainer.setVisibility(View.VISIBLE);
                startLocationUpdates();
            }
        } else {
            Toast.makeText(this, "Location permission required", Toast.LENGTH_SHORT).show();
        }
    }
}