Comparison framework for mobile congestion control (Bachelor Thesis) Pascal Suter

# Initial install:
# Android app:
    Install Android Studio and open the folder mobilecca.
    To run the app on the phone, the phone requires android API 24 (Android 7.0) or higher. The phone must be rooted and permission to use a superuser shell must be granted to the app.
    The app can be installed onto any compatible phone through Android Studio.
    Install the app MagicIperf from google play (https://play.google.com/store/apps/details?id=com.nextdoordeveloper.miperf.miperf&hl=en).
    
# Python server:
    Requires python 3.7 or newer.
    Install following libraries: tkinter (https://wiki.python.org/moin/TkInter), pyshark (https://pypi.org/project/pyshark/) and default libraries (e.g. socket, sys, threading etc).
    Install iPerf3 (https://iperf.fr/). The location of the install is not important, the command to call iperf must be specified in the server.
    Configure the permissions on the computer running the server such that any command "sudo tc ..." can be executed without requiring a password.
    The port of the socket server can be specified in the file server.py.


# Use of the framework:
The structure of the control messages that are exchanged between phones and server can be seen in the file "server/structures.txt"
# Android app:
    When first starting the app or by pressing the "change settings" button, settings can be changed.
    Enter a name for the device (must not contain ",") and the IP address and port number of the server.
    The port of the server can be specified in the file server.py.

# Python server:
    To start the server, go to the directory "server/" and run the module server.py.
    The port of the socket server can be specified in the file server.py.
    The following commands must be executed after each restart of the computer:
    $ sudo modprobe ifb
    $ sudo ip link set dev ifb0 up
    When first running the server, go to "Server settings" and specify the command to run iPerf as well as the network device/interface on which the phone will connect to the server (e.g. eth0). All available interfaces can be viewed by entering the following command into the terminal:
    $ ip link show