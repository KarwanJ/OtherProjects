package com.example.pathtracker;

import android.location.OnNmeaMessageListener;
import androidx.appcompat.widget.SwitchCompat;
import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.location.GnssStatus;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.preference.PreferenceManager;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.TextView;
import android.widget.Toast;
import androidx.activity.EdgeToEdge;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import com.google.android.material.tabs.TabLayout;
import org.osmdroid.config.Configuration;
import org.osmdroid.tileprovider.tilesource.TileSourceFactory;
import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.MapController;
import org.osmdroid.views.MapView;
import org.osmdroid.views.overlay.Marker;
import org.osmdroid.views.overlay.Polygon;
import org.osmdroid.views.overlay.Polyline;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;

public class MapActivity extends AppCompatActivity {

    // Map-related components
    MapView map;
    TabLayout tabLayout;
    FrameLayout bottomPanel;
    View layoutLocation, layoutSpeedRecord, layoutAccuracy;

    // UI components
    Button btn_update;
    TextView lat, lon, speed, liveLat, liveLon, locationStatus, accuracyText, newAccuracyText;
    MapController mapController;
    LocationManager locationManager;
    LocationListener locationListener;
    private static final String TAG = "OsmActivity";
    Polygon accuracyCircle;
    Marker userMarker;
    private boolean isRecording = false;
    private List<GeoPoint> coords = new ArrayList<>();
    private List<Polyline> allPaths = new ArrayList<>();
    Location previousLocation;
    long previousTime;
    Polyline pathPolyline;
    private GnssStatus.Callback gnssStatusCallback;
    private int satelliteCount = 0;
    SwitchCompat switch_record;
    SwitchCompat switchSmoothSpeed;
    private float smoothedSpeed = 0f;
    private float currentHdop = -1f;
    private float currentPdop = -1f;
    private float currentVdop = -1f;
    private static final int DEFAULT_FILL_COLOR = 0x220000FF;
    private static final int DEFAULT_STROKE_COLOR = 0xFF0000FF;
    private static final int ERROR_FILL_COLOR = 0xFFFF0000;
    private static final int ERROR_STROKE_COLOR = 0xFFFF0000;
    TextView dopValuesText;
    RadioGroup radioGroupAccuracyMode;
    RadioButton radioIndoor, radioOutdoor, radioOff;

    private final OnNmeaMessageListener nmeaListener = new OnNmeaMessageListener() {
        @Override
        public void onNmeaMessage(@NonNull String message, long timestamp) {
            if (message.startsWith("$GPGSA")) {
                String[] parts = message.split(",");
                try {
                    currentPdop = Float.parseFloat(parts[15]);
                    currentHdop = Float.parseFloat(parts[16]);
                    currentVdop = Float.parseFloat(parts[17].split("\\*")[0]);
                    Log.d("NMEA", "HDOP: " + currentHdop + ", VDOP: " + currentVdop + ", PDOP: " + currentPdop);
                    runOnUiThread(() -> {
                        dopValuesText.setText(String.format("HDOP: %.2f | VDOP: %.2f | PDOP: %.2f", currentHdop, currentVdop, currentPdop));
                    });
                } catch (Exception e) {
                    Log.e("NMEA", "Parse error: " + e.getMessage());
                }
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_map);

        btn_update = findViewById(R.id.btn_update);
        Button btnCenterLocation = findViewById(R.id.btn_center_location);
        lat = findViewById(R.id.textView_lat);
        lon = findViewById(R.id.textView_long);
        liveLat = findViewById(R.id.textView_live_lat);
        liveLon = findViewById(R.id.textView_live_long);
        speed = findViewById(R.id.textView_speed);
        locationStatus = findViewById(R.id.location_status);
        switch_record = findViewById(R.id.switch_record);
        accuracyText = findViewById(R.id.textView_accuracy);
        newAccuracyText = findViewById(R.id.textView_new_accuracy);
        switchSmoothSpeed = findViewById(R.id.switch_smooth_speed);
        dopValuesText = findViewById(R.id.textView_dop_values);
        tabLayout = findViewById(R.id.tab_layout);
        bottomPanel = findViewById(R.id.bottom_info_panel);
        layoutLocation = findViewById(R.id.layout_location);
        layoutSpeedRecord = findViewById(R.id.layout_speed_record);
        layoutAccuracy = findViewById(R.id.layout_accuracy);
        radioGroupAccuracyMode = findViewById(R.id.radio_group_accuracy_mode);
        radioIndoor = findViewById(R.id.radio_indoor);
        radioOutdoor = findViewById(R.id.radio_outdoor);
        radioOff = findViewById(R.id.radio_off);

        // Add OnCheckedChangeListener to RadioGroup
        radioGroupAccuracyMode.setOnCheckedChangeListener((group, checkedId) -> {
            float adjustedAccuracy = 0f;
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                Location lastKnownLocation = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
                if (lastKnownLocation != null) {
                    float androidAccuracy = lastKnownLocation.getAccuracy();
                    float uere = 5.0f;
                    adjustedAccuracy = (currentHdop > 0) ? currentHdop * uere : androidAccuracy;
                }
            }
            updateAccuracyCircleColor(adjustedAccuracy);
        });

        tabLayout.addTab(tabLayout.newTab().setText("Location"));
        tabLayout.addTab(tabLayout.newTab().setText("Speed/Record"));
        tabLayout.addTab(tabLayout.newTab().setText("Accuracy"));

        tabLayout.addOnTabSelectedListener(new TabLayout.OnTabSelectedListener() {
            @Override
            public void onTabSelected(TabLayout.Tab tab) {
                bottomPanel.setVisibility(View.VISIBLE);
                layoutLocation.setVisibility(View.GONE);
                layoutSpeedRecord.setVisibility(View.GONE);
                layoutAccuracy.setVisibility(View.GONE);
                switch (tab.getPosition()) {
                    case 0:
                        layoutLocation.setVisibility(View.VISIBLE);
                        break;
                    case 1:
                        layoutSpeedRecord.setVisibility(View.VISIBLE);
                        break;
                    case 2:
                        layoutAccuracy.setVisibility(View.VISIBLE);
                        break;
                }
            }

            @Override
            public void onTabUnselected(TabLayout.Tab tab) {
            }

            @Override
            public void onTabReselected(TabLayout.Tab tab) {
                if (bottomPanel.getVisibility() == View.VISIBLE) {
                    bottomPanel.setVisibility(View.GONE);
                    layoutLocation.setVisibility(View.GONE);
                    layoutSpeedRecord.setVisibility(View.GONE);
                    layoutAccuracy.setVisibility(View.GONE);
                } else {
                    bottomPanel.setVisibility(View.VISIBLE);
                    switch (tab.getPosition()) {
                        case 0:
                            layoutLocation.setVisibility(View.VISIBLE);
                            break;
                        case 1:
                            layoutSpeedRecord.setVisibility(View.VISIBLE);
                            break;
                        case 2:
                            layoutAccuracy.setVisibility(View.VISIBLE);
                            break;
                    }
                }
            }
        });

        btnCenterLocation.setOnClickListener(v -> {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                Location lastKnownLocation = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
                if (lastKnownLocation != null) {
                    GeoPoint userLocation = new GeoPoint(lastKnownLocation.getLatitude(), lastKnownLocation.getLongitude());
                    mapController.setCenter(userLocation);
                    mapController.setZoom(20);
                    map.setMapOrientation(0f);
                    map.invalidate();
                } else {
                    Toast.makeText(this, "Current location is not available", Toast.LENGTH_SHORT).show();
                }
            }
        });

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        map = findViewById(R.id.mapview);
        map.setUseDataConnection(true);
        Context ctx = getApplicationContext();
        Configuration.getInstance().load(ctx, PreferenceManager.getDefaultSharedPreferences(ctx));
        Configuration.getInstance().setUserAgentValue(getPackageName());

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            List<String> permissions = new ArrayList<>();
            if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                permissions.add(Manifest.permission.ACCESS_FINE_LOCATION);
            }
            if (checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                permissions.add(Manifest.permission.WRITE_EXTERNAL_STORAGE);
            }
            if (!permissions.isEmpty()) {
                ActivityCompat.requestPermissions(this, permissions.toArray(new String[0]), 1);
            }
        }

        map.getTileProvider().clearTileCache();
        map.setTileSource(TileSourceFactory.MAPNIK);
        map.setBuiltInZoomControls(true);
        map.setMultiTouchControls(true);
        mapController = (MapController) map.getController();
        mapController.setZoom(20);
        map.setMapOrientation(0f);
        GeoPoint center = new GeoPoint(35.711522, 51.381414);
        mapController.setCenter(center);
        map.invalidate();

        locationManager = (LocationManager) getSystemService(LOCATION_SERVICE);
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED
                && ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{
                    Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION
            }, 100);
        }

        userMarker = new Marker(map);
        userMarker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER);
        userMarker.setTitle("My Location");
        userMarker.setRotation(0f);
        userMarker.setIcon(getResources().getDrawable(R.drawable.arrow_marker));

        pathPolyline = new Polyline();
        pathPolyline.setColor(0xFF0000FF);
        pathPolyline.setWidth(5f);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            gnssStatusCallback = new GnssStatus.Callback() {
                @Override
                public void onSatelliteStatusChanged(@NonNull GnssStatus status) {
                    satelliteCount = status.getSatelliteCount();
                }
            };
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                locationManager.registerGnssStatusCallback(gnssStatusCallback);
            }
        }

        View loadingContainer = findViewById(R.id.loading_container);

        locationListener = new LocationListener() {
            @Override
            public void onLocationChanged(@NonNull Location location) {
                if (loadingContainer.getVisibility() == View.VISIBLE) {
                    loadingContainer.setVisibility(View.GONE);
                }

                double latitude = location.getLatitude();
                double longitude = location.getLongitude();

                liveLat.setText(String.format("Live Lat: %.5f", latitude));
                liveLon.setText(String.format("Live Lon: %.5f", longitude));

                GeoPoint point = new GeoPoint(latitude, longitude);
                userMarker.setPosition(point);
                if (!map.getOverlays().contains(userMarker)) {
                    map.getOverlays().add(userMarker);
                }
                mapController.setCenter(point);

                if (accuracyCircle != null) {
                    map.getOverlays().remove(accuracyCircle);
                }

                float androidAccuracy = location.getAccuracy();
                accuracyText.setText(String.format("Accuracy (getAccuracy): %.2f m", androidAccuracy));

                float uere = 5.0f;
                float accuracyRadius;
                String labelText;

                if (currentHdop > 0) {
                    accuracyRadius = currentHdop * uere;
                    labelText = String.format("HDOP Accuracy: %.2f m", accuracyRadius);
                } else {
                    accuracyRadius = androidAccuracy;
                    labelText = String.format("Fallback Accuracy: %.2f m", accuracyRadius);
                }
                newAccuracyText.setText(labelText);

                double zoomLevel = map.getZoomLevelDouble();
                float adjustedAccuracy = accuracyRadius;

                accuracyCircle = new Polygon();
                accuracyCircle.setPoints(Polygon.pointsAsCircle(point, adjustedAccuracy));
                accuracyCircle.setStrokeWidth(2f);
                map.getOverlays().add(accuracyCircle);
                updateAccuracyCircleColor(adjustedAccuracy);

                if (isRecording) {
                    coords.add(point);
                    pathPolyline.setPoints(coords);
                    if (!map.getOverlays().contains(pathPolyline)) {
                        map.getOverlays().add(pathPolyline);
                    }
                    map.invalidate();
                }

                if (previousLocation != null) {
                    float distance = location.distanceTo(previousLocation);
                    long timeDelta = location.getTime() - previousTime;

                    if (distance >= 1.0 && timeDelta > 0) {
                        float rawSpeed = (distance / timeDelta) * 1000;

                        if (switchSmoothSpeed.isChecked()) {
                            if (rawSpeed > smoothedSpeed * 3 && rawSpeed > 10f) {
                                rawSpeed = smoothedSpeed;
                            }
                            float alpha = 0.3f;
                            smoothedSpeed = alpha * rawSpeed + (1 - alpha) * smoothedSpeed;
                            float SmoothspeedKmh = smoothedSpeed * 3.6f;
                            speed.setText(String.format("Speed (Smoothed): %.2f m/s (%.2f km/h)", smoothedSpeed, SmoothspeedKmh));
                        } else {
                            float rawspeedKmh = rawSpeed * 3.6f;
                            speed.setText(String.format("Speed: %.2f m/s (%.2f km/h)", rawSpeed, rawspeedKmh));
                        }
                    } else {
                        speed.setText("Speed: 0.00 m/s");
                    }

                    double lat1 = Math.toRadians(previousLocation.getLatitude());
                    double lon1 = Math.toRadians(previousLocation.getLongitude());
                    double lat2 = Math.toRadians(location.getLatitude());
                    double lon2 = Math.toRadians(location.getLongitude());

                    double dLon = lon2 - lon1;
                    double y = Math.sin(dLon) * Math.cos(lat2);
                    double x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);

                    double azimuthRad = Math.atan2(y, x);
                    double azimuthDeg = (Math.toDegrees(azimuthRad) + 360) % 360;

                    map.setMapOrientation((float) -azimuthDeg);
                }

                previousLocation = location;
                previousTime = location.getTime();
            }
        };

        try {
            locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000, 1, locationListener);
        } catch (Exception e) {
            e.printStackTrace();
        }

        switch_record.setOnCheckedChangeListener((buttonView, isChecked) -> {
            isRecording = isChecked;
            handleSwitchChange();
        });

        btn_update.setOnClickListener(v -> {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                Location lastKnownLocation = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
                if (lastKnownLocation != null) {
                    lat.setText(String.format("%.5f", lastKnownLocation.getLatitude()));
                    lon.setText(String.format("%.5f", lastKnownLocation.getLongitude()));
                }
            }
        });
    }

    private void updateAccuracyCircleColor(float adjustedAccuracy) {
        boolean isIndoor = radioIndoor != null && radioIndoor.isChecked();
        boolean isOutdoor = radioOutdoor != null && radioOutdoor.isChecked();
        boolean isOff = radioOff != null && radioOff.isChecked();

        if (isOff) {
            accuracyCircle.setFillColor(DEFAULT_FILL_COLOR);
            accuracyCircle.setStrokeColor(DEFAULT_STROKE_COLOR);
        } else if (isIndoor && adjustedAccuracy > 10f) {
            accuracyCircle.setFillColor(ERROR_FILL_COLOR);
            accuracyCircle.setStrokeColor(ERROR_STROKE_COLOR);
        } else if (isOutdoor && adjustedAccuracy > 5f) {
            accuracyCircle.setFillColor(ERROR_FILL_COLOR);
            accuracyCircle.setStrokeColor(ERROR_STROKE_COLOR);
        } else {
            accuracyCircle.setFillColor(DEFAULT_FILL_COLOR);
            accuracyCircle.setStrokeColor(DEFAULT_STROKE_COLOR);
        }

        map.invalidate();
    }

    private float[] calculateDOP() {
        float hdop = 5.0f;
        float gdop = 7.5f;
        float uere = 5.0f;
        float accuracyRadius2 = (float) (Math.sqrt(hdop * hdop + gdop * gdop) * uere);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N && satelliteCount >= 4) {
            float avgElevation = 45.0f;
            float sinEl = (float) Math.sin(Math.toRadians(avgElevation));
            hdop = Math.max(1.0f, (float) (2.0 / (sinEl * Math.sqrt(satelliteCount))));
            gdop = hdop * 1.5f;
            accuracyRadius2 = (float) (Math.sqrt(hdop * hdop + gdop * gdop) * uere);
        }

        return new float[]{accuracyRadius2};
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
            locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000, 1, locationListener);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                locationManager.addNmeaListener(nmeaListener);
                locationManager.registerGnssStatusCallback(gnssStatusCallback);
            }
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            locationManager.removeNmeaListener(nmeaListener);
            if (gnssStatusCallback != null) {
                locationManager.unregisterGnssStatusCallback(gnssStatusCallback);
            }
        }
    }

    private void handleSwitchChange() {
        Log.d("MapActivity", "handleSwitchChange called, isRecording: " + isRecording);
        if (isRecording) {
            Log.d("MapActivity", "Switch turned on, clearing coords and creating new polyline");
            coords.clear();
            pathPolyline = new Polyline();
            pathPolyline.setColor(0xFF0000FF);
            pathPolyline.setWidth(5f);
            map.getOverlays().add(pathPolyline);
            allPaths.add(pathPolyline);
            Log.d("MapActivity", "New polyline added to overlays, allPaths size: " + allPaths.size());
        } else {
            Log.d("MapActivity", "Switch turned off, coords size: " + coords.size());
            if (!coords.isEmpty()) {
                try {
                    Log.d("MapActivity", "Attempting to save shapefile");
                    writeShapefile(coords);
                    Log.d("MapActivity", "Shapefile saved successfully");
                    Log.d("MapActivity", "Attempting to save GeoJSON");
                    writeGeoJSON(coords);
                    Log.d("MapActivity", "GeoJSON saved successfully");
                } catch (IOException e) {
                    Log.e("MapActivity", "IOException while saving file: " + e.getMessage(), e);
                    Toast.makeText(this, "Error saving file: " + e.getMessage(), Toast.LENGTH_LONG).show();
                } catch (Exception e) {
                    Log.e("MapActivity", "Unexpected error while saving file: " + e.getMessage(), e);
                    Toast.makeText(this, "Unexpected error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                }
            } else {
                Log.d("MapActivity", "No coordinates to save");
                Toast.makeText(this, "No coordinates available to save", Toast.LENGTH_SHORT).show();
            }
            coords.clear();
            Log.d("MapActivity", "Coords cleared for next recording");
        }
        map.invalidate();
        Log.d("MapActivity", "Map invalidated");
    }

    private File getStorageDirectory() throws IOException {
        File dir = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS), "PathTracker_Files");
        if (!dir.exists() && !dir.mkdirs()) {
            Log.e("MapActivity", "Failed to create directory: " + dir.getAbsolutePath());
            throw new IOException("Could not create directory: " + dir.getAbsolutePath());
        }
        Log.d("MapActivity", "Directory ready: " + dir.getAbsolutePath());
        return dir;
    }

    private void writeShapefile(List<GeoPoint> coords) throws IOException {
        if (coords == null || coords.isEmpty()) {
            Log.e("MapActivity", "No coordinates to save in shapefile");
            throw new IOException("No coordinates to save");
        }

        File dir = getStorageDirectory();
        String baseName = "path_" + System.currentTimeMillis();
        File shpFile = new File(dir, baseName + ".shp");
        File shxFile = new File(dir, baseName + ".shx");
        File dbfFile = new File(dir, baseName + ".dbf");
        File prjFile = new File(dir, baseName + ".prj");

        writeShp(coords, shpFile);
        writeShx(coords, shxFile);
        writeDbf(1, dbfFile);
        writePrj(prjFile);

        if (shpFile.exists() && shpFile.length() > 0 &&
                shxFile.exists() && shxFile.length() > 0 &&
                dbfFile.exists() && dbfFile.length() > 0 &&
                prjFile.exists() && prjFile.length() > 0) {
            Log.d("MapActivity", "Shapefile saved successfully: " + shpFile.getAbsolutePath());
            runOnUiThread(() -> Toast.makeText(this, "Shapefile saved: " + shpFile.getAbsolutePath(), Toast.LENGTH_LONG).show());
        } else {
            Log.e("MapActivity", "Failed to save shapefile: one or more files missing or empty");
            throw new IOException("Failed to save shapefile: one or more files missing or empty");
        }
    }

    private void writeShp(List<GeoPoint> coords, File file) throws IOException {
        try (FileOutputStream fos = new FileOutputStream(file);
             DataOutputStream out = new DataOutputStream(fos)) {
            double minX = Double.POSITIVE_INFINITY;
            double minY = Double.POSITIVE_INFINITY;
            double maxX = Double.NEGATIVE_INFINITY;
            double maxY = Double.NEGATIVE_INFINITY;

            for (GeoPoint p : coords) {
                double lon = p.getLongitude();
                double lat = p.getLatitude();
                minX = Math.min(minX, lon);
                maxX = Math.max(maxX, lon);
                minY = Math.min(minY, lat);
                maxY = Math.max(maxY, lat);
            }

            int contentLength = (44 + 4 + coords.size() * 16) / 2;

            out.writeInt(9994);
            for (int i = 0; i < 5; i++) out.writeInt(0);
            out.writeInt(50 + contentLength);
            out.writeInt(Integer.reverseBytes(1000));
            out.writeInt(Integer.reverseBytes(3));

            writeLEDouble(out, minX);
            writeLEDouble(out, minY);
            writeLEDouble(out, maxX);
            writeLEDouble(out, maxY);

            for (int i = 0; i < 4; i++) writeLEDouble(out, 0.0);

            out.writeInt(1);
            out.writeInt(contentLength);

            out.writeInt(Integer.reverseBytes(3));
            writeLEDouble(out, minX);
            writeLEDouble(out, minY);
            writeLEDouble(out, maxX);
            writeLEDouble(out, maxY);

            out.writeInt(Integer.reverseBytes(1));
            out.writeInt(Integer.reverseBytes(coords.size()));
            out.writeInt(Integer.reverseBytes(0));

            for (GeoPoint p : coords) {
                writeLEDouble(out, p.getLongitude());
                writeLEDouble(out, p.getLatitude());
            }
        }
    }

    private void writeShx(List<GeoPoint> coords, File file) throws IOException {
        try (FileOutputStream fos = new FileOutputStream(file);
             DataOutputStream out = new DataOutputStream(fos)) {
            int contentLength = (44 + 4 + coords.size() * 16) / 2;
            out.writeInt(9994);
            for (int i = 0; i < 5; i++) out.writeInt(0);
            out.writeInt(50 + 4);
            out.writeInt(Integer.reverseBytes(1000));
            out.writeInt(Integer.reverseBytes(3));
            double minX = coords.stream().mapToDouble(GeoPoint::getLongitude).min().orElse(0);
            double maxX = coords.stream().mapToDouble(GeoPoint::getLongitude).max().orElse(0);
            double minY = coords.stream().mapToDouble(GeoPoint::getLatitude).min().orElse(0);
            double maxY = coords.stream().mapToDouble(GeoPoint::getLatitude).max().orElse(0);
            writeLEDouble(out, minX);
            writeLEDouble(out, minY);
            writeLEDouble(out, maxX);
            writeLEDouble(out, maxY);
            for (int i = 0; i < 4; i++) writeLEDouble(out, 0.0);
            out.writeInt(50);
            out.writeInt(contentLength);
        }
    }

    private void writeDbf(int featureCount, File file) throws IOException {
        try (FileOutputStream fos = new FileOutputStream(file);
             DataOutputStream out = new DataOutputStream(fos)) {
            out.writeByte(3);
            out.writeByte(125 - 1900);
            out.writeByte(4);
            out.writeByte(22);
            out.writeInt(Integer.reverseBytes(featureCount));
            out.writeShort(Short.reverseBytes((short) 33));
            out.writeShort(Short.reverseBytes((short) 1));
            for (int i = 0; i < 20; i++) out.writeByte(0);
            out.writeBytes("ID");
            for (int i = 0; i < 9; i++) out.writeByte(0);
            out.writeByte('N');
            out.writeInt(0);
            out.writeByte(4);
            out.writeByte(0);
            for (int i = 0; i < 14; i++) out.writeByte(0);
            out.writeByte(0x0D);
            for (int i = 0; i < featureCount; i++) {
                out.writeByte(0x20);
                out.writeInt(Integer.reverseBytes(i + 1));
            }
        }
    }

    private void writePrj(File file) throws IOException {
        try (FileOutputStream fos = new FileOutputStream(file)) {
            String wgs84 = "GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223563]],PRIMEM[\"Greenwich\",0],UNIT[\"degree\",0.0174532925199433]]";
            fos.write(wgs84.getBytes());
        }
    }

    private void writeGeoJSON(List<GeoPoint> coords) throws IOException {
        if (coords == null || coords.isEmpty()) {
            Log.e("MapActivity", "No coordinates to save in GeoJSON");
            throw new IOException("No coordinates to save");
        }

        File dir = getStorageDirectory();
        File file = new File(dir, "path_" + System.currentTimeMillis() + ".geojson");

        try (FileOutputStream fos = new FileOutputStream(file)) {
            StringBuilder json = new StringBuilder();
            json.append("{\n");
            json.append("  \"type\": \"FeatureCollection\",\n");
            json.append("  \"features\": [\n");
            json.append("    {\n");
            json.append("      \"type\": \"Feature\",\n");
            json.append("      \"geometry\": {\n");
            json.append("        \"type\": \"LineString\",\n");
            json.append("        \"coordinates\": [\n");

            for (int i = 0; i < coords.size(); i++) {
                GeoPoint p = coords.get(i);
                json.append(String.format("          [%.6f, %.6f]", p.getLongitude(), p.getLatitude()));
                if (i < coords.size() - 1) json.append(",");
                json.append("\n");
            }

            json.append("        ]\n");
            json.append("      },\n");
            json.append("      \"properties\": {}\n");
            json.append("    }\n");
            json.append("  ]\n");
            json.append("}\n");

            fos.write(json.toString().getBytes());
        }

        if (file.exists() && file.length() > 0) {
            Log.d("MapActivity", "GeoJSON saved successfully: " + file.getAbsolutePath());
            runOnUiThread(() -> Toast.makeText(this, "GeoJSON saved: " + file.getAbsolutePath(), Toast.LENGTH_LONG).show());
        } else {
            Log.e("MapActivity", "Failed to save GeoJSON: file missing or empty");
            throw new IOException("Failed to save GeoJSON: file missing or empty");
        }
    }

    private void writeLEDouble(DataOutputStream out, double value) throws IOException {
        ByteBuffer buffer = ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN);
        buffer.putDouble(value);
        out.write(buffer.array());
    }

    public boolean isLocationPermissionGranted() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                Log.v(TAG, "Location permission is granted");
                return true;
            } else {
                Log.v(TAG, "Location permission is revoked");
                ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, 1);
                return false;
            }
        } else {
            Log.v(TAG, "Location permission is granted");
            return true;
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            Log.v(TAG, "Permission: " + permissions[0] + " was " + grantResults[0]);
        }
    }
}