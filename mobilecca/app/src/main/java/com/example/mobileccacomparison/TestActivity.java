package com.example.mobileccacomparison;

import androidx.appcompat.app.AppCompatActivity;

import android.content.res.AssetManager;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;


public class TestActivity extends AppCompatActivity {

    public static ConcurrentLinkedQueue<String> q;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_test);
    }

    public void onTest(View view) {
        String res = runIperf("192.168.1.127", "5201");
        set_txt(res);
    }

    public void onTest2(View view) {
        String res = String.valueOf(Util.getBatteryLevel(this));
        set_txt(res);
}

    public String runIperf(String ip, String port) {
        String appFileDirectory = getFilesDir().getPath();
        String iperf_cmd = "./iperf3 -c " + ip + " -p " + port;
        //String[] cmds = {"cd " + appFileDirectory, "./iperf3 -c 192.168.1.127 -p 5201"}; //./iperf3 -c 192.168.1.127 -p 5201
        String[] cmds = {"cd /data/data/com.nextdoordeveloper.miperf.miperf/files/", iperf_cmd};


        return Util.run_cmds(cmds, true);
    }

    private void set_txt(String txt) {
        TextView textview = findViewById(R.id.textView6);
        textview.setText(txt);
    }



}
