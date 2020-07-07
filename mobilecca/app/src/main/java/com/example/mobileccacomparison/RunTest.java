package com.example.mobileccacomparison;

import android.content.Context;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;

public class RunTest extends Thread {

    public String name;
    private int number_cca;
    private String[] ccas;
    private String iperf_cmd;
    private String length;
    private String[] tmp_results_files;
    public String[] results_files;
    public String debug = "";

    public RunTest(String name, String length, String ip, String port, int number_cca, String[] ccas) {
        this.name = name;
        this.number_cca = number_cca;
        this.ccas = ccas;
        iperf_cmd = "./data/data/com.nextdoordeveloper.miperf.miperf/files/iperf3 -c " + ip + " -p " + port + " -t " + length;
        this.length = length;
        tmp_results_files = new String[number_cca];
    }

    @Override
    public void run() {
        String tcp_length = String.valueOf(Integer.parseInt(length) + 1); //let tcpdump run longer than iperf to not cutoff last packages
        String[] iperf_res = new String[number_cca];
        for (int i = 0; i < number_cca; i++) {
            String[] cmds = {Util.set_cca(ccas[i]), iperf_cmd};
            RunTCPdump tcp = new RunTCPdump(Util.appDir, tcp_length, i);
            tcp.start();
            iperf_res[i] = Util.run_cmds(cmds, true);
            try {
                tcp.join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            tmp_results_files[i] = tcp.tcpdump_save;
        }

        process_Data(iperf_res);
    }

    /**
     * processes data generated by the test run and saves it in files specified in field results_files. Currently just saves everything
     * @param iperf_res values returned by iperf
     */
    public void process_Data(String[] iperf_res) {
        //TODO better data processing
        String iperf_res_file_tmp = "iperf_res.txt";
        String iperf_res_file = "/sdcard/" + Config.current.name + "_iperf_res.txt";
        try {
            FileOutputStream fOut = Util.cont.openFileOutput(iperf_res_file_tmp, Context.MODE_PRIVATE);
            OutputStreamWriter osw = new OutputStreamWriter(fOut);
            osw.write(Util.stringArray_toString(iperf_res, "\n"));
            osw.close();
        } catch (FileNotFoundException e) {
            debug = "1, " + e.toString();
            return;
        } catch (IOException e) {
            debug = "2, " + e.toString();
            return;
        }

        Util.run_cmds(new String[]{"cd " + Util.appDir, "cp " + iperf_res_file_tmp + " " + iperf_res_file}, false);
        results_files = new String[tmp_results_files.length + 1];
        results_files[0] = iperf_res_file;
        for (int i = 1; i <= tmp_results_files.length; i++) {
            results_files[i] = tmp_results_files[i-1];
        }

    }


    public class RunTCPdump extends Thread {
        /**
         * class that runs tcpdump
         * https://www.tcpdump.org/manpages/tcpdump.1.html for information about options
         */
        String appFileDirectory;
        String tcp_cmd;
        String tcpdump_save;
        public RunTCPdump(String appFileDirectory, String length, int runNumber) {
            this.appFileDirectory = appFileDirectory;
            tcpdump_save = "/sdcard/" + Config.current.name + "_dump_run" + runNumber + ".pcap";
            //length of tcpdump specified according to https://stackoverflow.com/questions/25731643/how-to-schedule-tcpdump-to-run-for-a-specific-period-of-time
            tcp_cmd = "./tcpdump -i any -s 0 -G " + length + " -W 1 -w " + tcpdump_save;

        }

        @Override
        public void run() {
            String[] cmds = {"cd "+ appFileDirectory, tcp_cmd};
            Util.run_cmds(cmds, false);
        }

    }

}