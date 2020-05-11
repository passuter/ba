package com.example.mobileccacomparison;

import androidx.appcompat.app.AppCompatActivity;

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
        String name = Config.current.name;
        dev_name.setText(name);
        EditText ip = findViewById(R.id.editIP);
        ip.setText(Config.current.ip);

        EditText port = findViewById(R.id.editPort);
        port.setText(Integer.toString(Config.current.port));

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

        if (error_occurred) {
            Intent error_intent = new Intent(this, ChangeConfigErrorActivity.class);
            startActivity(error_intent);
        } else {
            String[] cca = Util.get_cca();
            Config.current = new Config(name, ip, port, cca);
            Config.save_config(this);

            Intent home = new Intent(this, HomeActivity.class);
            startActivity(home);
        }

    }
}
