package com.example.mobileccacomparison;

public class RunTest extends Thread {

    public String name;
    private String[] cmds;


    public class RunTCPdump extends Thread {
        /**
         * class that runs tcpdump
         * https://www.tcpdump.org/manpages/tcpdump.1.html for information about options
         */
        String appFileDirectory;
        String tcp_cmd;
        public RunTCPdump(String appFileDirectory, String length, int runNumber) {
            this.appFileDirectory = appFileDirectory;
            String tcpdump_save = "/sdcard/dump_run" + runNumber + ".pcap";
            //length of tcpdump specified according to https://stackoverflow.com/questions/25731643/how-to-schedule-tcpdump-to-run-for-a-specific-period-of-time
            tcp_cmd = "./tcpdump -i any -s 0 -G " + length + " -W 1 -w " + tcpdump_save;

        }

        @Override
        public void run() {
            String tcpdump_save = "/sdcard/dump.pcap";
            String[] cmds = {"cd "+ appFileDirectory, tcp_cmd};
            Util.run_cmds(cmds, false);
        }

    }


    public RunTest(String name, String length, String ip, String port, int number_cca, String[] ccas) {
        this.name = name;
        cmds = new String[1 + 2*number_cca]; //1 cmd to change directory, 2 cmds per testrun (1 to change cca, 1 to start iperf)
        cmds[0] = "cd " + Util.appDir;
        for (int i = 0; i < number_cca; i++) {
            cmds[2*i + 1] = Util.set_cca(ccas[i]);
            cmds[2*i+2] = "iperf3.7 -c " + ip + " -p " + port + " -t " + length;
        }
    }

    @Override
    public void run() {
        Util.run_cmds(cmds, false);
    }
}
