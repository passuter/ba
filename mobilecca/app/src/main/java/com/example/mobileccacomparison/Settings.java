package com.example.mobileccacomparison;

import android.content.Context;
import android.util.Log;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;

public class Settings {
    public static Settings current;

    public static final String default_name = "No_name";

    public String name;
    public String ip;
    public int port;
    public int battery_measurement_interval; //wait time between measurements in seconds
    public String[] cca;

    public Settings() {
        this(default_name, "0.0.0.0", 0, 60, new String[0]);
    }

    public Settings(String name, String ip, int port, int battery_measurement_interval, String[] congestion_algos) {
        this.name = name;
        this.ip = ip;
        this.port = port;
        this.battery_measurement_interval = battery_measurement_interval;
        this.cca = congestion_algos;
    }

    /**
     * Loads the configuration from config.txt if possible, otherwise loads default values.
     * @return true if loading from config.txt succeeded, false if default values were loaded
     */
    public static boolean init(Context context) {
        current = load_config(context);
        return !default_name.equals(current.name);
    }

    /**
     * Checks wheter there is a valid current configuration
     * @return
     */
    public static boolean isValid() {
        return !(current == null || current.name == default_name);
    }


    /**
     * Loads a configuration from the config.txt file
     * @param context
     * @return Config loaded from config.txt or the default Config should the load fail
     */
    public static Settings load_config(Context context) {
        Settings conf;
        try {
            FileInputStream fIn = context.openFileInput("config.txt");
            InputStreamReader isr = new InputStreamReader(fIn);
            int length = 2048;
            char[] buffer = new char[length];
            isr.read(buffer);
            String[] lines = (new String(buffer)).split("\n");
            String name = lines[0];
            String ip = lines[1];
            int port = Integer.parseInt(lines[2]);
            int measuring_interval;
            try {
                measuring_interval = Integer.parseInt(lines[3]);
            } catch (Exception e) {
                //could not read measuring interval, set to default
                measuring_interval = 60;
            }
            String[] ccas = Util.get_cca();
            conf = new Settings(name, ip, port, measuring_interval, ccas);
        } catch (IOException e) {
            conf = new Settings();
        }
        return conf;
    }

    /**
     * Saves the current configuration into config.txt
     * @param context
     */
    public static void save_config(Context context) {
        try {
            FileOutputStream fOut = context.openFileOutput("config.txt", Context.MODE_PRIVATE);
            OutputStreamWriter osw = new OutputStreamWriter(fOut);
            StringBuilder sb = new StringBuilder();
            sb.append(Settings.current.name).append("\n");
            sb.append(Settings.current.ip).append("\n");
            sb.append(Settings.current.port).append("\n");
            sb.append(Settings.current.battery_measurement_interval).append("\n");
            String data = sb.toString();
            osw.write(data);
            osw.close();
        }
        catch (IOException e) {
            //TODO maybe improve error handling
            Log.e("Exception", "File write failed: " + e.toString());
        }
    }

    public static String asString() {
        StringBuilder sb = new StringBuilder();
        sb.append(current.name);
        for (int i = 0; i<current.cca.length; i++) {
            sb.append(",").append(current.cca[i]);
        }
        return sb.toString();
    }
}
