package com.example.mobileccacomparison;

/**
 * Author: Pascal Suter
 * This class is used to establish a connection with the server using sockets.
 */

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.util.concurrent.ConcurrentLinkedQueue;

public class Connection extends Thread{

    private static Connection c = null;

    private ConcurrentLinkedQueue<String> queue;
    private boolean running = true;
    private RunTest test = null;

    private Connection(ConcurrentLinkedQueue<String>q) {
        queue = q;
    }

    /**
     * Sets up and dispatches a Connection thread, which will connect & communicate to the server
     * @param queue queue to communicate with main thread
     */
    public static void connect(ConcurrentLinkedQueue<String> queue) {
        if (c != null) {
            try {
                if (c.running) {
                    queue.offer("Server already running");
                    return;
                } else {
                    c.join();
                    c = null;
                }
            } catch (Exception e) {//InterruptedException e) {
                c.print_Exception(e);
                return;
            }
        }

        c = new Connection(queue);
        try {
            c.start();
        } catch (Exception e) {
            c.print_Exception(e);
        }
    }

    private void close(Socket socket) {
        try {
            if (socket!=null) {
                socket.close();
            }
        } catch (IOException e) {
            print_Exception(e);
        }
        queue.offer("Connection closed");
        //Todo implement closing a connection
    }

    /**
     * Closes the current connection, should be called from the main thread and not the Connection thread
     */
    public static void end_connection() {
        if (c == null) {
            return;
        }

        c.running = false;
        try {
            c.join();
            c = null;
            return;
        } catch (InterruptedException e) {
            c.print_Exception(e);
            return;
        }
    }

    @Override
    public void run() {

        Socket socket = null;
        BufferedReader recv = null;
        DataOutputStream send = null;
        try {
            socket = new Socket(Settings.current.ip, Settings.current.port);
            send = new DataOutputStream(socket.getOutputStream());
            recv = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            socket.setSoTimeout(500);
            //queue.offer("Socket established"); //debug only

            String line = "";
            send.writeUTF(",10," + Settings.asString());

            while (running) {
                try {
                    line = recv.readLine();
                    String response = handle_msg(line);
                    if (!response.equals("")) {
                        send.writeUTF(response);
                    }
                } catch (SocketTimeoutException e) {
                    //no message received, nothing to do
                }
            }

        } catch (RuntimeException | IOException e) {
            print_Exception(e);
        }
        close(socket);
    }

    /**
     * Reads and reacts to a received message
     * @param msg
     * @return response message to be sent back or "" if nothing to send back
     */
    private String handle_msg(String msg) {
        String[] msg_split = msg.split(",");
        //read type of message
        int type = Integer.parseInt(msg_split[1]);
        //copy msg data into new array
        String[] data = new String[msg_split.length-2];
        System.arraycopy(msg_split, 2, data, 0, msg_split.length - 2);
        String response = "";
        switch (type) {
            case 2: break;
            case 4: running = false; break;
            case 11: queue.offer("Connected to server"); break;
            case 20: response = handle_msg20(data); break;
            default: queue.offer("Could not handle a received message");
        }
        return response;
    }

    private String handle_msg20(String[] data) {
        String response;
        try {
            String name = data[0];
            String length = data[1];
            boolean is_battery_test = data[2].equals("True");
            String ip = data[3];
            String port = data[4];
            int number_cca = Integer.parseInt(data[5]);
            String[] ccas = new String[number_cca];
            System.arraycopy(data, 6, ccas, 0, number_cca);
            if (test != null) {
                throw new RuntimeException("Test is already running");
            }
            test = new RunTest(name, length, is_battery_test, ip, port, number_cca, ccas);
            test.start();
            queue.offer("Running test " + name);
            test.join();
            String num_files = String.valueOf(test.results_files.length);
            String file_res = Util.stringArray_toString(test.results_files, ",");
            test = null; //test completed, can be removed
            response = ",21," + num_files + "," + file_res; //write back success
            queue.offer("Finished test " + name);
        } catch (RuntimeException | InterruptedException e) {
            response = ",21,0," + e.toString();
        }
        return response;
    }

    private void print_Exception(Exception e) {
        queue.offer(e.toString());
    }
}