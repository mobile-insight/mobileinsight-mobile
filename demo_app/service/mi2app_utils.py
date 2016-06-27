"""
mi2app_utils.py

Define utility variables and functions for apps.
"""

# FIXME (likayo): subprocess module in Python 2.7 is not thread-safe.
# Use subprocess32 instead.
import subprocess as sp
import os
import re

from jnius import autoclass

ANDROID_SHELL    = "/system/bin/sh"

# This one works with Pygame, current bootstrap
PythonService    = autoclass('org.renpy.android.PythonService')

# This one works with SDL2
# PythonActivity = autoclass('org.kivy.android.PythonActivity')
# PythonService  = autoclass('org.kivy.android.PythonService')

pyService        = PythonService.mService
androidOsBuild   = autoclass("android.os.Build")
Context          = autoclass('android.content.Context')
File             = autoclass("java.io.File")
FileOutputStream = autoclass('java.io.FileOutputStream')
ConnManager      = autoclass('android.net.ConnectivityManager')
mWifiManager     = pyService.getSystemService(Context.WIFI_SERVICE);


def run_shell_cmd(cmd, wait = False):
    p = sp.Popen("su", executable = ANDROID_SHELL, shell = True, stdin = sp.PIPE, stdout = sp.PIPE)
    res, err = p.communicate(cmd + '\n')
    if wait:
        p.wait()
        return res
    else:
        return res

def get_PythonService():
    return PythonService

def get_cache_dir():
    return str(PythonService.getCacheDir().getAbsolutePath())

def get_files_dir():
    return str(PythonService.getFilesDir().getAbsolutePath())

def get_phone_manufacturer():
    return androidOsBuild.MANUFACTURER

def get_phone_model():
    return androidOsBuild.MODEL

def get_phone_info():
    cmd          = "getprop ro.product.model; getprop ro.product.manufacturer;"
    res          = run_shell_cmd(cmd).split('\n')
    model        = res[0].replace(" ", "")
    manufacturer = res[1].replace(" ", "")
    phone_info   = get_device_id() + '_' + manufacturer + '-' + model
    return phone_info

def get_operator_info():
    cmd          = "getprop gsm.operator.alpha"
    operator     = run_shell_cmd(cmd).split('\n')[0].replace(" ", "")
    if operator == '' or operator is None:
        operator = 'null'
    return operator

def get_device_id():
    cmd          = "service call iphonesubinfo 1"
    out          = run_shell_cmd(cmd)
    tup          = re.findall("\'.+\'", out)
    tupnum       = re.findall("\d+", "".join(tup))
    deviceId     = "".join(tupnum)
    return deviceId

def get_mobile_insight_path():
    """
    Return the root path of MobileInsight, or None if not accessible
    """

    Environment = autoclass("android.os.Environment")
    state = Environment.getExternalStorageState()
    if not Environment.MEDIA_MOUNTED == state:
        return None

    sdcard_path = Environment.getExternalStorageDirectory().toString()
    mobile_insight_path = os.path.join(sdcard_path, "mobile_insight")
    return mobile_insight_path

def get_mobile_insight_log_path():
    """
    Return the log path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path, "log")

def get_mobile_insight_log_decoded_path():
    """
    Return the decoded log path of MobileInsight, or None if not accessible
    """

    log_path = get_mobile_insight_log_path()

    if not log_path:
        return None

    return os.path.join(log_path, "decoded")

def get_mobile_insight_log_uploaded_path():
    """
    Return the uploaded log path of MobileInsight, or None if not accessible
    """

    log_path = get_mobile_insight_log_path()

    if not log_path:
        return None

    return os.path.join(log_path, "uploaded")

def get_mobile_insight_cfg_path():
    """
    Return the configuration path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path, "cfg")

def get_mobile_insight_db_path():
    """
    Return the database path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path, "cfg")

def get_mobile_insight_plugin_path():
    """
    Return the plugin path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path, "apps")

def get_mobile_insight_crash_log_path():
    """
    Return the plugin path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path, "crash_logs")


def get_wifi_status():
    return mWifiManager.isWifiEnabled()