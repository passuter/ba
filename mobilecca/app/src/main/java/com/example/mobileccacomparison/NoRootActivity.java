package com.example.mobileccacomparison;

import androidx.appcompat.app.AppCompatActivity;

import android.os.Bundle;
import android.widget.TextView;


public class NoRootActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_no_root);
        /* used for debugging
        String tmp = Util.check_root_debug();
        TextView test_view = findViewById(R.id.textView2);
        test_view.setText(tmp);
         */
    }
}
