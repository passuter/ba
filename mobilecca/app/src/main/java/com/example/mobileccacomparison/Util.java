package com.example.mobileccacomparison;


import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;

public class Util {

    private static String config_save_file = "config.txt";

    public static final int MAX_PORT = 65535;

    /**
     * Runs a command on a su shell
     * @param command command to execute
     * @return string of response from the shell
     */
    public static String run_cmd(String command) {
        Process p;
        StringBuilder res = new StringBuilder();
        try {
            p = Runtime.getRuntime().exec("su");
            BufferedWriter w = new BufferedWriter(new OutputStreamWriter(p.getOutputStream()));
            BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String end = "/shell_end/";
            w.write(command + "\n");
            w.write("echo " + end + "\n");
            w.flush();
            String line;
            while ((line=r.readLine()) != null) {
                if (line.equals(end)) {
                    w.write("exit\n");
                    w.close();
                    break;
                }
                res.append("\n").append(line);
            }
        } catch (IOException e) {
            //TODO: add error handling
        }
        return res.toString();
    }

    /**
     * Sets a congestion control algorithm.
     * @param cca algorithm to be set.
     */
    public static void set_cca(String cca) {
        run_cmd("sysctl -w net.ipv4.tcp_congestion_control=" + cca);
    }

    /**
     * Gets available congestion control algorithms
     * @return array of available ccas
     */
    public static String[] get_cca() {
        return run_cmd("cat /proc/sys/net/ipv4/tcp_available_congestion_control").split(" ");
    }

    /**
     * Checks if the app has root permission
     * @return true if app has root permission
     */
    public static boolean check_root() {
        String test_string = "has_root_test";
        String res = run_cmd("echo " + test_string);
        res = res.trim(); //removes tailing newline
        return test_string.equals(res);
    }

    public static String check_root_debug() {
        String test_string = "has_root_test";
        String res = run_cmd("echo " + test_string);
        return res;
    }

    public static class Connection {

        public static void connect(HomeActivity home) {

        }
    }
}
