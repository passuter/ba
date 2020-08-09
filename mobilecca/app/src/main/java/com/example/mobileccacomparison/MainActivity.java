package com.example.mobileccacomparison;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;


public class MainActivity extends AppCompatActivity {


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }

    /**
     * Checks for root permission (may block until root has been granted). Then tries to load the device configuration.
     * If it succeeds, opens the Home activity, else opens directly the ChangeConfig activity.
     * @param view
     */
    public void onCheckRoot(View view) {
        if (Util.check_root()) {
            init();
            if (Settings.init(this)) {
                Intent intent = new Intent(this, HomeActivity.class);
                startActivity(intent);
            } else {
                //no config loaded, go directly to ChangeConfig
                Intent intent = new Intent(this, ChangeConfigActivity.class);
                startActivity(intent);
            }
        } else {
            Intent intent = new Intent(this, NoRootActivity.class);
            startActivity(intent);
        }
    }

    private void init() {
        Util.init(this);
        Util.copyIperf3(this);
        Util.copyTCPDump(this);
        Util.copyAssets("iperf3.XXXXXX", this);
    }
}
