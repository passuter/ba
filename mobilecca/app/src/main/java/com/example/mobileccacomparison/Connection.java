package com.example.mobileccacomparison;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.Socket;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.util.concurrent.BlockingDeque;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentLinkedQueue;

public class Connection extends Thread{

    private static Connection c = null;

    private ConcurrentLinkedQueue<String> queue;
    private boolean running = true;

    private Connection(ConcurrentLinkedQueue<String>q) {
        queue = q;
    }

    /**
     * Sets up and dispatches a Connection thread, which will connect & communicate to the server
     * @param queue
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
            socket.close();
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
            socket = new Socket(Config.current.ip, Config.current.port);
            send = new DataOutputStream(socket.getOutputStream());
            recv = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            socket.setSoTimeout(500);
            queue.offer("Socket established"); //debug only

            String line = "";
            send.writeUTF(",10," + Config.asString());

            while (running) {
                try {
                    line = recv.readLine();
                    handle_msg(line);
                } catch (SocketTimeoutException e) {
                    //no message received, nothing to do
                }
            }

        } catch (RuntimeException | IOException e) {
            print_Exception(e);
        }
        close(socket);
    }

    private void handle_msg(String msg) {
        String[] msg_split = msg.split(",");
        //read type of message
        int type = Integer.parseInt(msg_split[1]);
        //copy msg data into new array
        String[] data = new String[msg_split.length-2];
        for (int i = 2; i < msg_split.length; i++) {
            data[i-2] = msg_split[i];
        }
        switch (type) {
            case 2: break;
            case 4: running = false; break;
            case 11: queue.offer("Connected to server"); break;
            case 20: handle_msg20(data); break;
            default: queue.offer("Could not handle a received message");
        }
    }

    private void handle_msg20(String[] data) {
        //TODO implement receiving a test configuration
        queue.offer("Received Test-configuration " + data[0]);
    }

    private void print_Exception(Exception e) {
        queue.offer(e.toString());
    }
}