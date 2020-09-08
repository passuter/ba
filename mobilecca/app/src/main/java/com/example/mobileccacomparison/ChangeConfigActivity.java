package com.example.mobileccacomparison;

/**
 * Author: Pascal Suter
 * This class
 */

import androidx.appcompat.app.AppCompatActivity;

/**
 * Author: Pascal Suter
 * This class creates the screen that the user can use to change the settings of the phone
 */

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;

public class ChangeConfigActivity extends AppCompatActivity {

    public static String ERROR_MESSAGE = "No error";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_change_config);
        EditText dev_name = findViewById(R.id.editDevName);
        String name = Settings.current.name;
        dev_name.setText(name);
        EditText ip = findViewById(R.id.editIP);
        ip.setText(Settings.current.ip);
        EditText port = findViewById(R.id.editPort);
        port.setText(Integer.toString(Settings.current.port));
        EditText battery = findViewById(R.id.editBtry);
        battery.setText(Integer.toString(Settings.current.battery_measurement_interval));

    }

    public void onOK(View view) {
        boolean error_occurred = false;

        EditText name_edit = findViewById(R.id.editDevName);
        String name = name_edit.getText().toString();

        EditText ip_edit = findViewById(R.id.editIP);
        String ip = ip_edit.getText().toString();
        //TODO check if entered ip address is valid

        EditText port_edit = findViewById(R.id.editPort);
        String port_str = port_edit.getText().toString();
        int port = -1;
        try {
            port = Integer.parseInt(port_str);
        } catch (RuntimeException e) {
            ERROR_MESSAGE = "Entered value for port could not be converted to integer. Entry was " + port_str;
            error_occurred = true;
        }
        if ((port < 0 || port >= Util.MAX_PORT) && !error_occurred) {
            ERROR_MESSAGE = "Invalid port number, has to be between 0 and " + Util.MAX_PORT + ", was " + port;
            error_occurred = true;
        }
        int battery_interval = -1;
        try {
            EditText btry_edit = findViewById(R.id.editBtry);
            String battery_interval_raw = btry_edit.getText().toString();
            battery_interval = Integer.parseInt(battery_interval_raw);
            if (battery_interval <= 0) {
                throw new RuntimeException();
            }
        } catch (RuntimeException e) {
            String error_msg = "Entered value for battery_interval is invalid, must be integer > 0";
            if (error_occurred) {
                ERROR_MESSAGE = ERROR_MESSAGE + "\n" + error_msg; //append second error message to first
            } else {
                ERROR_MESSAGE = error_msg;
                error_occurred = true;
            }
        }

        if (error_occurred) {
            Intent error_intent = new Intent(this, ChangeConfigErrorActivity.class);
            startActivity(error_intent);
        } else {
            String[] cca = Util.get_cca();
            Settings.current = new Settings(name, ip, port, battery_interval, cca);
            Settings.save_config(this);

            Intent home = new Intent(this, HomeActivity.class);
            startActivity(home);
        }

    }
}
