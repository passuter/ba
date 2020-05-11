package com.example.mobileccacomparison;

import androidx.appcompat.app.AppCompatActivity;

import android.os.Bundle;
import android.widget.TextView;

public class ChangeConfigErrorActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_change_config_error);
        TextView text = findViewById(R.id.textView5);
        text.setText(ChangeConfigActivity.ERROR_MESSAGE);
    }
}
