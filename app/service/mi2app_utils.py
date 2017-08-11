"""
mi2app_utils.py

Define utility variables and functions for apps.
"""

# FIXME (likayo): subprocess module in Python 2.7 is not thread-safe.
# Use subprocess32 instead.
import subprocess as sp
import os
import re
import jnius
from jnius import autoclass, cast, PythonJavaClass, java_method

ANDROID_SHELL = "/system/bin/sh"

# This one works with Pygame, current bootstrap
PythonService = autoclass('org.renpy.android.PythonService')

# This one works with SDL2
# PythonActivity = autoclass('org.kivy.android.PythonActivity')
# PythonService  = autoclass('org.kivy.android.PythonService')

pyService = PythonService.mService
androidOsBuild = autoclass("android.os.Build")
Context = autoclass('android.content.Context')
File = autoclass("java.io.File")
FileOutputStream = autoclass('java.io.FileOutputStream')
ConnManager = autoclass('android.net.ConnectivityManager')
mWifiManager = pyService.getSystemService(Context.WIFI_SERVICE)

def run_shell_cmd(cmd, wait=False):
    p = sp.Popen(
        "su",
        executable=ANDROID_SHELL,
        shell=True,
        stdin=sp.PIPE,
        stdout=sp.PIPE)
    res, err = p.communicate(cmd + '\n')
    if wait:
        p.wait()
        return res
    else:
        return res


def get_service_context():
    return pyService


def get_cache_dir():
    return str(pyService.getCacheDir().getAbsolutePath())


def get_files_dir():
    return str(pyService.getFilesDir().getAbsolutePath())


def get_phone_manufacturer():
    return androidOsBuild.MANUFACTURER


def get_phone_model():
    return androidOsBuild.MODEL


def get_phone_info():
    cmd = "getprop ro.product.model; getprop ro.product.manufacturer;"
    res = run_shell_cmd(cmd)
    if not res:
        return get_device_id() + '_null-null'
    res = res.split('\n')
    model = res[0].replace(" ", "")
    manufacturer = res[1].replace(" ", "")
    phone_info = get_device_id() + '_' + manufacturer + '-' + model
    return phone_info


def get_operator_info():
    cmd = "getprop gsm.operator.alpha"
    operator = run_shell_cmd(cmd).split('\n')[0].replace(" ", "")
    if operator == '' or operator is None:
        operator = 'null'
    return operator


def get_device_id():
    cmd = "service call iphonesubinfo 1"
    out = run_shell_cmd(cmd)
    tup = re.findall("\'.+\'", out)
    tupnum = re.findall("\d+", "".join(tup))
    deviceId = "".join(tupnum)
    return deviceId


def get_sdcard_path():
    """
    Return the sdcard path of MobileInsight, or None if not accessible
    """
    Environment = autoclass("android.os.Environment")
    state = Environment.getExternalStorageState()
    if not Environment.MEDIA_MOUNTED == state:
        return None

    sdcard_path = Environment.getExternalStorageDirectory().toString()
    return sdcard_path


def get_mobileinsight_path():
    """
    Return the root path of MobileInsight, or None if not accessible
    """

    Environment = autoclass("android.os.Environment")
    state = Environment.getExternalStorageState()
    if not Environment.MEDIA_MOUNTED == state:
        return None

    sdcard_path = Environment.getExternalStorageDirectory().toString()
    mobileinsight_path = os.path.join(sdcard_path, "mobileinsight")
    return mobileinsight_path


def get_mobileinsight_log_path():
    """
    Return the log path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "log")


def get_mobileinsight_analysis_path():
    """
    Return the analysis result path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "analysis")


def get_mobileinsight_log_decoded_path():
    """
    Return the decoded log path of MobileInsight, or None if not accessible
    """

    log_path = get_mobileinsight_log_path()

    if not log_path:
        return None

    return os.path.join(log_path, "decoded")


def get_mobileinsight_log_uploaded_path():
    """
    Return the uploaded log path of MobileInsight, or None if not accessible
    """

    log_path = get_mobileinsight_log_path()

    if not log_path:
        return None

    return os.path.join(log_path, "uploaded")


def get_mobileinsight_cfg_path():
    """
    Return the configuration path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "cfg")


def get_mobileinsight_db_path():
    """
    Return the database path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "dbs")


def get_mobileinsight_plugin_path():
    """
    Return the plugin path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "plugins")


def get_mobileinsight_crash_log_path():
    """
    Return the plugin path of MobileInsight, or None if not accessible
    """

    mobileinsight_path = get_mobileinsight_path()

    if not mobileinsight_path:
        return None

    return os.path.join(mobileinsight_path, "crash_logs")


def get_wifi_status():
    return mWifiManager.isWifiEnabled()

def detach_thread():
    try:
        jnius.detach()
    except BaseException:
        pass



# Get GPS Location
LocationManager = autoclass('android.location.LocationManager')
cur_latitude = None
cur_longitude = None
class MiLocationListener(PythonJavaClass):
    """
    An Python-version android.location.LocationListener (https://developer.android.com/reference/android/location/LocationListener.html).
    To implement it, we use Pyjnius's reflection class
    Reference: http://pyjnius.readthedocs.io/en/latest/api.html#java-class-implementation-in-python
    """
    __javainterfaces__ = ['android/location/LocationListener']

    def __init__(self):
        super(MiLocationListener, self).__init__()

    @java_method('(Landroid/location/Location;)V')
    def onLocationChanged(self, location):

        """
        javap -s -bootclasspath ./android.jar android.location.LocationListener
        Compiled from "LocationListener.java"
        public interface android.location.LocationListener {
          public abstract void onLocationChanged(android.location.Location);
            descriptor: (Landroid/location/Location;)V

          public abstract void onStatusChanged(java.lang.String, int, android.os.Bundle);
            descriptor: (Ljava/lang/String;ILandroid/os/Bundle;)V

          public abstract void onProviderEnabled(java.lang.String);
            descriptor: (Ljava/lang/String;)V

          public abstract void onProviderDisabled(java.lang.String);
            descriptor: (Ljava/lang/String;)V
        }
        """
        # print location.getLatitude(), location.getLongitude()
        print "Get New Location!",location.getLatitude(), location.getLongitude()
        cur_latitude = location.getLatitude()
        cur_longitude = location.getLongitude()

    @java_method('(Ljava/lang/String;ILandroid/os/Bundle;)V')
    def onStatusChanged(self, provider, status, extras):
        pass
    @java_method('(Ljava/lang/String;)V')
    def onProviderEnabled(self, provider):
        pass
    @java_method('(Ljava/lang/String;)V')
    def onProviderDisabled(self, provider):
        pass


def get_last_known_location():
    locMan = pyService.getSystemService(Context.LOCATION_SERVICE)
    location = locMan.getLastKnownLocation(LocationManager.GPS_PROVIDER)
    if not location:
        location = locMan.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
    if location:
        return (location.getLatitude(),location.getLongitude())
    else:
        return None

location_listener_registered = False
def register_location_listener():
    global location_listener_registered
    if not location_listener_registered:
    	HandlerThread = autoclass('android.os.HandlerThread')
    	handler_t = HandlerThread('Location Requester')
    	handler_t.start()
        locManager = pyService.getSystemService(Context.LOCATION_SERVICE)
        locationListener = MiLocationListener()
        locManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 0, 0, locationListener, handler_t.getLooper())
        location_listener_registered = True

def get_current_location():
    if not cur_longitude or not cur_latitude:
        return get_last_known_location()
    else:
        return (cur_latitude, cur_longitude)

    
