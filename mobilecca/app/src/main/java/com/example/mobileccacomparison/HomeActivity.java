package com.example.mobileccacomparison;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

import java.util.concurrent.ConcurrentLinkedQueue;

public class HomeActivity extends AppCompatActivity {

    private static ConcurrentLinkedQueue<String> q;
    private static String display_msg;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);
        String txt_name = "Device name: " + Settings.current.name;
        TextView textViewName = findViewById(R.id.textViewName);
        textViewName.setText(txt_name);
        String txt_addr = "Server address: (" + Settings.current.ip + ", " + Settings.current.port + ")";
        TextView textViewAddr = findViewById(R.id.textViewAddr);
        textViewAddr.setText(txt_addr);

        if (q == null) {
            q = new ConcurrentLinkedQueue<>();
            set_info("Ready to connect", "");
        }
    }

    public void onChange(View view) {
        Intent intent = new Intent(this, ChangeConfigActivity.class);
        startActivity(intent);
    }

    public void onConnect(View view) {
        if (!Settings.isValid()) {
            q.offer("No configuration set, cannot connect to server");
            return;
        }

        Connection.connect(q);
    }

    public void onGetMessage(View view) {
        String str = q.poll();
        if (str == null) {
            set_info(display_msg, "No new message. ");
        } else {
            set_info(str, "");
        }
    }

    public void onDisconnect(View view) {
        //TODO implement closing a connection
        Connection.end_connection();
    }

    /**
     * Displays a message on home window
     * @param txt second part of message, will be saved in static field to be reused.
     * @param insert first part of message
     */
    public void set_info(String txt, String insert) {
        display_msg = txt;
        TextView info = findViewById(R.id.connectionInfo);
        info.setText(insert + txt);
    }

    public void onTest(View view) {
        startActivity(new Intent(this, TestActivity.class));
    }
}
