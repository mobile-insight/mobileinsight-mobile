# How to install and use this app #

1. Create a "ws_dissector" folder under the "/data" folder of your phone. Copy the follwoing files into it:

    android_pie_ws_dissector
    libglib-2.0.so
    libgmodule-2.0.so
    libgobject-2.0.so
    libgthread-2.0.so
    libwireshark.so.5
    libwiretap.so.4
    libwsutil.so.4

Then change the permissions of all files to 755, including the "/data/ws_dissector" folder itself.

2. Put under the "/sdcard/diag_logs" directory a "Diag.cfg" file that suits your need

3. Run the app. Usually it will ask for root permission for the first time, and will immediately crash after that. This behavior is normal and should disappear from the second time running.

4. Click "Start/Stop collection" buttons to control the collection process. The app will print out infomation about the current serving cell.
