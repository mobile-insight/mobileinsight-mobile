"""
main_utils.py

Define utility variables and functions for apps.
"""

from jnius import autoclass, cast

# FIXME(likayo): subprocess module in Python 2.7 is not thread-safe. Use subprocess32 instead.
import functools
import os
import shlex
import sys
import subprocess
import time
import traceback
import re
import datetime
import shutil
import stat
import json

current_activity = cast("android.app.Activity", autoclass("org.renpy.android.PythonActivity").mActivity)
ANDROID_SHELL = "/system/bin/sh"

File = autoclass("java.io.File")
FileOutputStream = autoclass('java.io.FileOutputStream')

def get_cur_version():
    """
    Get current apk version string
    """
    pkg_name = current_activity.getPackageName()
    return str(current_activity.getPackageManager().getPackageInfo(pkg_name, 0).versionName)

def run_shell_cmd(cmd, wait = False):
    p = subprocess.Popen("su", executable=ANDROID_SHELL, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    res,err = p.communicate(cmd+'\n')

    if wait:
        p.wait()
        return res
    else:
        return res

def get_sdcard_path():
    """
    Return the sdcard path of MobileInsight, or None if not accessible
    """
    Environment = autoclass("android.os.Environment")
    state = Environment.getExternalStorageState()
    if not Environment.MEDIA_MOUNTED==state:
        return None

    sdcard_path = Environment.getExternalStorageDirectory().toString()
    return sdcard_path

def get_mobile_insight_path():
    """
    Return the root path of MobileInsight, or None if not accessible
    """
    sdcard_path = get_sdcard_path()
    if not sdcard_path:
        return None

    mobile_insight_path = os.path.join(sdcard_path,"mobile_insight")
    return mobile_insight_path

def get_mobile_insight_log_path():
    """
    Return the log path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path,"log")

def get_mobile_insight_analysis_path():
    """
    Return the analysis result path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path,"analysis")

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

    return os.path.join(mobile_insight_path,"cfg")

def get_mobile_insight_db_path():
    """
    Return the database path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path,"cfg")

def get_mobile_insight_plugin_path():
    """
    Return the plugin path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path,"apps")

def get_mobile_insight_crash_log_path():
    """
    Return the plugin path of MobileInsight, or None if not accessible
    """

    mobile_insight_path = get_mobile_insight_path()

    if not mobile_insight_path:
        return None

    return os.path.join(mobile_insight_path,"crash_logs")


def get_cache_dir():
    return str(current_activity.getCacheDir().getAbsolutePath())


def get_files_dir():
    return str(current_activity.getFilesDir().getAbsolutePath())


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
