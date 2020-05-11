package com.example.mobileccacomparison;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentLinkedQueue;

public class HomeActivity extends AppCompatActivity {

    private static ConcurrentLinkedQueue<String> q;
    private static String display_msg;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);
        String txt_name = "Device name: " + Config.current.name;
        TextView textViewName = findViewById(R.id.textViewName);
        textViewName.setText(txt_name);
        String txt_addr = "Server address: (" + Config.current.ip + ", " + Config.current.port + ")";
        TextView textViewAddr = findViewById(R.id.textViewAddr);
        textViewAddr.setText(txt_addr);

        if (q == null) {
            q = new ConcurrentLinkedQueue<>();
            set_info("Ready to connect", "CCA0: " + Config.current.cca[0]);
        }
    }

    public void onChange(View view) {
        Intent intent = new Intent(this, ChangeConfigActivity.class);
        startActivity(intent);
    }

    public void onConnect(View view) {
        //TODO implement onConnect
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
}
