package com.example.mobileccacomparison;


import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.res.AssetManager;
import android.os.BatteryManager;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;

public class Util {

    public static final int MAX_PORT = 65535;
    public static String appDir; //files directory of the app
    public static Context cont; //makes the context of the app globally accessible


    public static void init(Context context) {
        appDir = context.getFilesDir().getPath();
        cont = context;
    }

    /**
     * Runs a command on a su shell
     *
     * @param command command to execute
     * @param printError whether to append the error output of the shell to return string
     * @return string of response from the shell
     */
    public static String run_cmd(String command, boolean printError) {
        Process p;
        StringBuilder res = new StringBuilder();
        String result;
        try {
            p = Runtime.getRuntime().exec("su");
            BufferedWriter w = new BufferedWriter(new OutputStreamWriter(p.getOutputStream()));
            BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
            BufferedReader error = new BufferedReader(new InputStreamReader(p.getErrorStream()));
            String end = "/shell_end/";
            w.write(command + "\n");
            w.write("echo " + end + "\n");
            w.flush();
            String line;
            while ((line = r.readLine()) != null) {
                if (line.equals(end)) {
                    w.write("exit\n");
                    w.close();
                    break;
                }
                res.append("\n").append(line);
            }
            if (printError) {
                while ((line = error.readLine()) != null) {
                    res.append("\nError: ").append(line);
                }
            }
            result = res.toString();
        } catch (IOException e) {
            //TODO: add error handling
            result = e.toString();
        }
        return result;
    }

    public static int getBatteryLevel(Context context) {
        IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        Intent batteryStatus = context.registerReceiver(null, ifilter);
        int level = batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
        int scale = batteryStatus.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
        float batteryPct = level * 100 / (float)scale;
        return  level;
    }

    /**
     * Runs a command on a su shell without returning the error messages
     * @param command command to execute
     * @return string of response from the shell
     */
    public static String run_cmd(String command) {
        return run_cmd(command, false);
    }

    /**
     * run multiple commands on a su shell
     * @return "" if nothing executed, otherwise response from the shell
     */
    public static String run_cmds(String[] commands, boolean printError) {
        if (commands == null || commands.length == 0) {
            return "";
        } else {
            StringBuilder sb = new StringBuilder();
            sb.append(commands[0]);
            for (int i = 1; i < commands.length; i++) {
                sb.append("\n").append(commands[i]);
            }
            return run_cmd(sb.toString(), printError);
        }
    }

    /**
     * run multiple commands on a su shell
     * @return "" if nothing executed, otherwise response from the shell
     */
    public static String run_cmds(String[] commands) {
        return run_cmds(commands, false);
    }

    /**
     * Sets a congestion control algorithm.
     *
     * @param cca algorithm to be set.
     * @return string cmd to set cca
     */
    public static String set_cca(String cca) {
        return "sysctl -w net.ipv4.tcp_congestion_control=" + cca;
    }

    /**
     * Gets available congestion control algorithms
     *
     * @return array of available ccas
     */
    public static String[] get_cca() {
        String[] ccas = run_cmd("cat /proc/sys/net/ipv4/tcp_available_congestion_control").split(" ");
        for (int i = 0; i < ccas.length; i++) {
            ccas[i] = ccas[i].trim();//remove whitespaces and newline characters
        }
        return  ccas;
    }

    /**
     * Checks if the app has root permission
     *
     * @return true if app has root permission
     */
    public static boolean check_root() {
        String test_string = "has_root_test";
        String res = run_cmd("echo " + test_string);
        res = res.trim(); //removes tailing newline
        return test_string.equals(res);
    }

    /**
     * Writes an array of strings into a single string using a separator
     * @param arr
     * @param separator
     * @return
     */
    public static String stringArray_toString(String[] arr, String separator) {
        if (arr == null) {
            return "";
        }

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < arr.length; i++) {
            sb.append(arr[i]).append(separator);
        }
        return sb.toString();
    }

    /**
     * copies a file from the assets into the apps file directory and marks it as executable
     * @param filename
     * @param context
     * @return success or not
     */
    public static boolean copyAssets(String filename, Context context) {
        //copied partially from https://stackoverflow.com/questions/5583487/hosting-an-executable-within-android-application
        AssetManager assetManager = context.getAssets();
        String appFileDirectory = context.getFilesDir().getPath();

        InputStream in;
        OutputStream out;

        try {
            in = assetManager.open(filename);
            File outFile = new File(appFileDirectory, filename);
            out = new FileOutputStream(outFile);
            Util.copy(in, out);
            in.close();
            out.flush();
            out.close();
            outFile.setExecutable(true);
        } catch(IOException e) {
            return false;
        }

        return true;
    }

    public static boolean copyIperf3(Context context) {
        return copyAssets("iperf3", context);
    }

    public static boolean copyTCPDump(Context context) {
        return copyAssets("tcpdump", context);
    }

    public static boolean deleteFile(String filename, Context context) {
        String appFileDirectory = context.getFilesDir().getPath();
        File f = new File(appFileDirectory, filename);
        return f.delete();
    }

    /**
     * Reads all bytes from an input stream and writes them to an output stream.
     */
    public static long copy(InputStream source, OutputStream sink) throws IOException {
        //copied from java.nio.file.Files.java
        final int BUFFER_SIZE = 8192;
        long nread = 0L;
        byte[] buf = new byte[BUFFER_SIZE];
        int n;
        while ((n = source.read(buf)) > 0) {
            sink.write(buf, 0, n);
            nread += n;
        }
        return nread;

    }

}
