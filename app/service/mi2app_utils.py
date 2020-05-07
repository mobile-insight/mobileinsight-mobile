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
import hashlib
from jnius import autoclass, cast, PythonJavaClass, java_method

ANDROID_SHELL = "/system/bin/sh"

# This one works with Pygame, current bootstrap
#PythonService = autoclass('org.renpy.android.PythonService')

# This one works with SDL2
PythonActivity = autoclass('org.kivy.android.PythonActivity')
PythonService  = autoclass('org.kivy.android.PythonService')

pyService = PythonService.mService
androidOsBuild = autoclass("android.os.Build")
Context = autoclass('android.content.Context')
File = autoclass("java.io.File")
FileOutputStream = autoclass('java.io.FileOutputStream')
ConnManager = autoclass('android.net.ConnectivityManager')
mWifiManager = pyService.getSystemService(Context.WIFI_SERVICE)
telephonyManager = pyService.getSystemService(Context.TELEPHONY_SERVICE)
locationManager = pyService.getSystemService(Context.LOCATION_SERVICE)

def run_shell_cmd(cmd, wait=False):
    if isinstance(cmd, str):
        cmd = cmd.encode()
    p = sp.Popen(
        "su",
        executable=ANDROID_SHELL,
        shell=True,
        stdin=sp.PIPE,
        stdout=sp.PIPE)
    res, err = p.communicate(cmd + b'\n')
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
        return get_device_sn() + '_null-null'
    res = res.decode('utf-8').split('\n')
    model = res[0].replace(" ", "")
    manufacturer = res[1].replace(" ", "")
    phone_info = get_device_sn() + '_' + manufacturer + '-' + model
    return phone_info


def get_operator_info():
    # return telephonyManager.getNetworkOperatorName()+"-"+telephonyManager.getNetworkOperator()
    return telephonyManager.getNetworkOperator()


def get_device_id():
    cmd = "service call iphonesubinfo 1"
    out = run_shell_cmd(cmd)
    tup = re.findall(b"\'.+\'", out)
    tupnum = re.findall(b"\d+", b"".join(tup))
    deviceId = b"".join(tupnum)
    return hashlib.md5(deviceId).hexdigest()


def get_device_sn():
    cmd = "getprop ro.serialno"
    out = run_shell_cmd(cmd)
    if out != b"":
        deviceSn = hashlib.md5(out).hexdigest()
    else:
        deviceSn = hashlib.md5(b"FFFFFFFF").hexdigest()
    return deviceSn


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
def get_last_known_location():
    # print "get_last_known_location"
    # locationManager = pyService.getSystemService(Context.LOCATION_SERVICE)
    location = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
    if not location:
        location = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
    if location:
        return (location.getLatitude(),location.getLongitude())
    else:
        return None

def get_current_location():
    return get_last_known_location()
    
