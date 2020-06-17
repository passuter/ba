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
import java.util.concurrent.TimeoutException;


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
        RunTest t = new RunTest("Base", "3", "192.168.1.127", "5201", 2, new String[]{"reno", "cubic"});
        set_txt("Starting test run");
        t.start();
        int time = 0;
        boolean running = true;
        try {
            t.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        if (t.results_files == null) {
            set_txt("Finished, no results received, debug: " + t.debug);
        } else {
            StringBuilder sb = new StringBuilder();
            sb.append("Test has concluded. Results at:\n");
            for (int i = 0; i < t.results_files.length; i++) {
                sb.append(t.results_files[i]).append("\n");
            }
            sb.append("Debug: ").append(t.debug);
            set_txt(sb.toString());
        }
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
