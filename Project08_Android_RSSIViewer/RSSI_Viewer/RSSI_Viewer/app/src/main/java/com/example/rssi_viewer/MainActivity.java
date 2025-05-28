package com.example.rssi_viewer;

import android.view.View;
import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.telephony.*;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    // UI components
    private ListView btsListView;
    private ArrayAdapter<String> adapter;
    private ArrayList<String> btsInfoList;
    private ProgressBar progressBar;

    // Permission request code
    private static final int PERMISSION_REQUEST_CODE = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize ProgressBar
        progressBar = findViewById(R.id.progressBar);

        // Initialize ListView and Adapter
        btsListView = findViewById(R.id.btsListView);
        btsInfoList = new ArrayList<>();
        adapter = new ArrayAdapter<>(this, android.R.layout.simple_list_item_1, btsInfoList);
        btsListView.setAdapter(adapter);

        // Setup Refresh Button
        Button refreshButton = findViewById(R.id.refreshButton);
        refreshButton.setOnClickListener(v -> {
            // Clear the current list
            btsInfoList.clear();
            adapter.notifyDataSetChanged();

            // Show ProgressBar and delay for 1 second before loading new data
            progressBar.setVisibility(View.VISIBLE);
            Toast.makeText(this, "Refreshing, please wait...", Toast.LENGTH_SHORT).show();

            new android.os.Handler().postDelayed(() -> {
                loadBTSInfo(); // Load BTS info after delay
                progressBar.setVisibility(View.GONE); // Hide ProgressBar
            }, 1000);
        });

        // Check permissions and load data
        checkPermissionsAndLoadBTS();
    }

    // Check required permissions
    private void checkPermissionsAndLoadBTS() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED ||
                ActivityCompat.checkSelfPermission(this, Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) {

            // Request permissions if not granted
            ActivityCompat.requestPermissions(this, new String[]{
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.READ_PHONE_STATE
            }, PERMISSION_REQUEST_CODE);
        } else {
            loadBTSInfo();
        }
    }

    // Handle permission request result
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                loadBTSInfo(); // Load BTS info if permission granted
            } else {
                Toast.makeText(this, "Permission denied!", Toast.LENGTH_SHORT).show();
            }
        }
    }

    // Load BTS (cell tower) information
    private void loadBTSInfo() {
        TelephonyManager telephonyManager = (TelephonyManager) getSystemService(TELEPHONY_SERVICE);
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            return; // Permission not granted, exit
        }

        List<CellInfo> cellInfoList = telephonyManager.getAllCellInfo();
        btsInfoList.clear(); // Clear current list

        // To keep track of unique Cell IDs
        HashSet<Integer> seenCellIds = new HashSet<>();

        if (cellInfoList != null && !cellInfoList.isEmpty()) {
            for (CellInfo cellInfo : cellInfoList) {
                String info = "";
                int rssi = Integer.MIN_VALUE;
                int cellId = -1;

                // Process LTE cells
                if (cellInfo instanceof CellInfoLte) {
                    CellInfoLte lteInfo = (CellInfoLte) cellInfo;
                    rssi = lteInfo.getCellSignalStrength().getDbm();
                    cellId = lteInfo.getCellIdentity().getCi();
                    info = "LTE - RSSI: " + rssi + " dBm";

                    // Process GSM cells
                } else if (cellInfo instanceof CellInfoGsm) {
                    CellInfoGsm gsmInfo = (CellInfoGsm) cellInfo;
                    rssi = gsmInfo.getCellSignalStrength().getDbm();
                    cellId = gsmInfo.getCellIdentity().getCid();
                    info = "GSM - RSSI: " + rssi + " dBm";

                    // Process WCDMA (3G) cells
                } else if (cellInfo instanceof CellInfoWcdma) {
                    CellInfoWcdma wcdmaInfo = (CellInfoWcdma) cellInfo;
                    rssi = wcdmaInfo.getCellSignalStrength().getDbm();
                    cellId = wcdmaInfo.getCellIdentity().getCid();
                    info = "WCDMA (3G) - RSSI: " + rssi + " dBm";

                    // Process 5G NR cells
                } else if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q && cellInfo instanceof CellInfoNr) {
                    CellSignalStrength signalStrength = ((CellInfoNr) cellInfo).getCellSignalStrength();
                    if (signalStrength instanceof CellSignalStrengthNr) {
                        rssi = ((CellSignalStrengthNr) signalStrength).getDbm();
                        cellId = ((CellInfoNr) cellInfo).getCellIdentity().hashCode(); // Use hashCode for unique ID
                        info = "5G NR - RSSI: " + rssi + " dBm";
                    }
                }

                // Filter out invalid RSSI values and duplicate Cell IDs
                if (rssi < -30 && rssi > -120 && cellId != -1 && !seenCellIds.contains(cellId)) {
                    seenCellIds.add(cellId); // Mark Cell ID as seen
                    btsInfoList.add(info);   // Add BTS info to list (no Cell ID shown)
                }
            }
        } else {
            btsInfoList.add("No BTS Info Found!");
        }

        adapter.notifyDataSetChanged(); // Update the ListView
    }
}