package com.example.pathtracker;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Enable edge-to-edge display for immersive UI
        EdgeToEdge.enable(this);
        // Set the layout for the main activity (splash screen)
        setContentView(R.layout.activity_main);

        // Handle window insets to adjust padding for system bars (status bar, navigation bar)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        // Create a delayed task to transition to MapActivity after 3.5 seconds
        new Handler().postDelayed(new Runnable() {
            @Override
            public void run() {
                // Start MapActivity
                Intent movetomap1 = new Intent(MainActivity.this, MapActivity.class);
                startActivity(movetomap1);
                // Close MainActivity to prevent returning to it
                finish();
            }
        }, 2500); // Delay of 3500 milliseconds (3.5 seconds)
    }
}