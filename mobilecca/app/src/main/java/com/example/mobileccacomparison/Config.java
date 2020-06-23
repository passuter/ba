package com.example.mobileccacomparison;

import android.content.Context;
import android.util.Log;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;

public class Config {
    public static Config current;

    public static final String default_name = "No_name";

    public String name;
    public String ip;
    public int port;
    public String[] cca;

    public Config() {
        this(default_name, "0.0.0.0", 0, new String[0]);
    }

    public Config(String name, String ip, int port, String[] congestion_algos) {
        this.name = name;
        this.ip = ip;
        this.port = port;
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
    public static Config load_config(Context context) {
        Config conf;
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
            String[] ccas = Util.get_cca();
            for (int i = 0; i < ccas.length; i++) {
                ccas[i] = ccas[i].trim();
            }
            conf = new Config(name, ip, port, ccas);
        } catch (IOException e) {
            conf = new Config();
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
            sb.append(Config.current.name).append("\n");
            sb.append(Config.current.ip).append("\n");
            sb.append(Config.current.port).append("\n");
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
