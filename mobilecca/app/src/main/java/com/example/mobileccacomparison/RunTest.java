package com.example.mobileccacomparison;

/**
 * Author: Pascal Suter
 * This class runs a test
 */

import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;

import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.util.Set;

public class RunTest extends Thread {

    public String name; //name of the test
    private int number_cca;
    private String[] ccas;
    private String iperf_cmd; //shell command to start iperf
    private String length;
    private boolean is_battery_test;
    private String[] tmp_results_files; //file location/names of the tcp dump
    public String[] results_files; //file location/names after pre-processing the data
    public String debug = "";

    public RunTest(String name, String length, boolean is_battery_test, String ip, String port, int number_cca, String[] ccas) {
        this.name = name;
        this.number_cca = number_cca;
        this.ccas = ccas;
        iperf_cmd = "./data/data/com.nextdoordeveloper.miperf.miperf/files/iperf3 -c " + ip + " -p " + port + " -t " + length;
        if (is_battery_test) {
            iperf_cmd = iperf_cmd + " -i " + Settings.current.battery_measurement_interval;
        }
        this.length = length;
        this.is_battery_test = is_battery_test;
        tmp_results_files = new String[number_cca];
    }

    @Override
    public void run() {
        String tcp_length = String.valueOf(Integer.parseInt(length) + 2); //let measurments run longer than iperf to not cutoff last packages
        String[] iperf_res = new String[number_cca];
        for (int i = 0; i < number_cca; i++) {
            String[] cmds = {Util.set_cca(ccas[i]), iperf_cmd};
            MeasuringThread measuringThread;
            if (is_battery_test) {
                measuringThread = new BatteryMeasurements(tcp_length, i);
            } else {
                measuringThread = new RunTCPdump(tcp_length, i);
            }
            measuringThread.start();
            iperf_res[i] = Util.run_cmds(cmds, true);
            try {
                measuringThread.join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            tmp_results_files[i] = measuringThread.result_file;
        }

        process_Data(iperf_res);
    }

    /**
     * processes data generated by the test run and saves it in files specified in field results_files. Currently just saves everything
     * @param iperf_res values returned by iperf
     */
    public void process_Data(String[] iperf_res) {

        results_files = new String[tmp_results_files.length + 1];
        if (is_battery_test) {
            //battery tmp results are saved in file directory, copy to "/sdcard/"
            String[] copy_cmds = new String[tmp_results_files.length + 1];
            copy_cmds[0] = "cd " + Util.appDir;
            for (int i = 0; i < tmp_results_files.length; i++) {
                String file_dst = "/sdcard/" + tmp_results_files[i];
                results_files[i+1] = file_dst;
                copy_cmds[i+1] = "cp " + tmp_results_files[i] + " " + file_dst;
            }
            Util.run_cmds(copy_cmds);
        } else {
            //Tcp dump files don't need to be modified, just copy tmp_locations to results_files
            System.arraycopy(tmp_results_files, 0, results_files, 1, tmp_results_files.length);
        }

        String iperf_res_file_tmp = "iperf_res.txt";
        String iperf_res_file = "/sdcard/" + Settings.current.name + "_iperf_res.txt";
        results_files[0] = iperf_res_file;
        try {
            FileOutputStream fOut = Util.cont.openFileOutput(iperf_res_file_tmp, Context.MODE_PRIVATE);
            OutputStreamWriter osw = new OutputStreamWriter(fOut);
            osw.write(Util.stringArray_toString(iperf_res, "\n"));
            osw.close();
            fOut = Util.cont.openFileOutput("res_id.txt", Context.MODE_PRIVATE);
            osw = new OutputStreamWriter(fOut);
            String txt = Settings.current.name + "," + name + "\n" + Util.stringArray_toString(results_files, ",");
            osw.write(txt);
            osw.close();
        } catch (FileNotFoundException e) {
            debug = "1, " + e.toString();
            return;
        } catch (IOException e) {
            debug = "2, " + e.toString();
            return;
        }

        String[] copy_cmds = new String[]{"cd " + Util.appDir, "cp " + iperf_res_file_tmp + " " + iperf_res_file, "cp res_id.txt /sdcard/res_id.txt"};
        Util.run_cmds(copy_cmds);
    }

    public abstract class MeasuringThread extends Thread {
        /**
         * implementations of this class perform measurements during a test
         * field result_file contains the location of the file with the results (file location may be relative to appFileDirectory)
         */
        String appFileDirectory = Util.appDir;
        public String result_file;
    }

    public class RunTCPdump extends MeasuringThread {
        /**
         * class that runs tcpdump
         * https://www.tcpdump.org/manpages/tcpdump.1.html for information about options
         */
        String tcp_cmd;

        public RunTCPdump(String length, int runNumber) {
            result_file = "/sdcard/" + Settings.current.name + "_dump_run" + runNumber + ".pcap";
            //length of tcpdump specified according to https://stackoverflow.com/questions/25731643/how-to-schedule-tcpdump-to-run-for-a-specific-period-of-time
            tcp_cmd = "./tcpdump -i any -s 0 -G " + length + " -W 1 -w " + result_file;
        }

        @Override
        public void run() {
            String[] cmds = {"cd "+ appFileDirectory, tcp_cmd};
            Util.run_cmds(cmds, false);
        }

    }

    public  class BatteryMeasurements extends MeasuringThread {
        int length;
        int measuring_interval;

        /**
         * Constructs class that performs measurements of the battery
         * @param length length of the test in seconds
         * @param run_number
         */
        public BatteryMeasurements(String length, int run_number) {
            this.length = Integer.parseInt(length);
            this.result_file = Settings.current.name + "_battery_run" + run_number + ".txt";
            measuring_interval = Settings.current.battery_measurement_interval;
        }

        @Override
        public void run() {
            try {
                int time_passed = 0;
                FileOutputStream fOut = Util.cont.openFileOutput(result_file, Context.MODE_PRIVATE);
                OutputStreamWriter osw = new OutputStreamWriter(fOut);
                while (true) {
                    osw.write(get_measurement(time_passed));
                    if (time_passed >= length) {
                        break; //used break statement instead of while condition to avoid last sleep()
                    }
                    time_passed += measuring_interval;
                    sleep(measuring_interval * 1000);
                }
                osw.close();
            } catch (FileNotFoundException e) {
                e.printStackTrace();
            } catch (IOException e) {
                e.printStackTrace();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }

        /**
         * read battery stats (see https://developer.android.com/training/monitoring-device-state/battery-monitoring)
         * @param time_passed time after test started
         * @return battery measurement
         */
        public String get_measurement(int time_passed) {
            IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
            Intent batteryStatus = Util.cont.registerReceiver(null, ifilter);
            int status = batteryStatus.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
            boolean isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL;
            String charging_state;
            if (isCharging) {
                charging_state = "1";
            } else {
                charging_state = "0";
            }
            int level = batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
            int scale = batteryStatus.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
            float batteryPct = level * 100 / (float)scale;
            String res = time_passed + "," + batteryPct + "," + charging_state + ",\n";
            return res;
        }
    }
}
