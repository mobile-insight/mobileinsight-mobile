"""
main_utils.py

Define utility variables and functions for apps.
"""
import jnius
from jnius import autoclass, cast

# FIXME(likayo): subprocess module in Python 2.7 is not thread-safe. Use
# subprocess32 instead.
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

current_activity = cast("android.app.Activity", autoclass(
    "org.kivy.android.PythonActivity").mActivity)
ANDROID_SHELL = "/system/bin/sh"

File = autoclass("java.io.File")
FileOutputStream = autoclass('java.io.FileOutputStream')

Context = autoclass('android.content.Context')
telephonyManager = current_activity.getSystemService(Context.TELEPHONY_SERVICE)
androidOsBuild = autoclass("android.os.Build")

class ChipsetType:
    """
    Cellular modem type
    """
    QUALCOMM = 0
    MTK = 1


def get_cur_version():
    """
    Get current apk version string
    """
    pkg_name = current_activity.getPackageName()
    return str(
        current_activity.getPackageManager().getPackageInfo(
            pkg_name, 0).versionName)


def is_rooted():
    """
    Check if the phone has been rooted
    """
    su_binary_path = [
        "/sbin/",
        "/system/bin/",
        "/system/xbin/",
        "/data/local/xbin/",
        "/su/bin/",
        "/data/local/bin/",
        "/system/sd/xbin/",
        "/system/bin/failsafe/",
        "/data/local/"]

    for path in su_binary_path:
        if os.path.exists(path + "su"):
            return True

    return False


def run_shell_cmd(cmd, wait=False):
    p = subprocess.Popen(
        "su",
        executable=ANDROID_SHELL,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    res, err = p.communicate(cmd + '\n')

    if wait:
        p.wait()
        return res
    else:
        return res

def get_chipset_type():
    """
    Determine the type of the chipset

    :returns: an enum of ChipsetType
    """


    """
    MediaTek: [ro.board.platform]: [mt6735m]
    Qualcomm: [ro.board.platform]: [msm8084]
    """
    cmd = "getprop ro.board.platform;"
    res = run_shell_cmd(cmd)
    if res.startswith("mt"):
        return ChipsetType.MTK
    elif res.startswith("msm") or res.startswith("mdm"):
        return ChipsetType.QUALCOMM
    else:
        return None


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


def get_legacy_mobileinsight_path():
    """
    Return the root path of MobileInsight, or None if not accessible
    """
    sdcard_path = get_sdcard_path()
    if not sdcard_path:
        return None

    legacy_mobileinsight_path = os.path.join(sdcard_path, "mobile_insight")
    return legacy_mobileinsight_path


def get_mobileinsight_path():
    """
    Return the root path of MobileInsight, or None if not accessible
    """
    sdcard_path = get_sdcard_path()
    if not sdcard_path:
        return None

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


def detach_thread():
    try:
        jnius.detach()
    except BaseException:
        pass


def get_cache_dir():
    return str(current_activity.getCacheDir().getAbsolutePath())


def get_files_dir():
    return str(current_activity.getFilesDir().getAbsolutePath())

def get_phone_manufacturer():
    return androidOsBuild.MANUFACTURER


def get_phone_model():
    return androidOsBuild.MODEL

def get_phone_info():
    # cmd = "getprop ro.product.model; getprop ro.product.manufacturer;"
    # res = run_shell_cmd(cmd)
    # if not res:
    #     return get_device_id() + '_null-null'
    # res = res.split('\n')
    # model = res[0].replace(" ", "")
    # manufacturer = res[1].replace(" ", "")
    # phone_info = get_device_id() + '_' + manufacturer + '-' + model
    phone_info = get_device_id() + '-' + get_phone_manufacturer() + '-' + get_phone_model()
    return phone_info

def get_operator_info():
    return telephonyManager.getNetworkOperatorName()+"-"+telephonyManager.getNetworkOperator()


def get_device_id():
    cmd = "service call iphonesubinfo 1"
    out = run_shell_cmd(cmd)
    tup = re.findall("\'.+\'", out)
    tupnum = re.findall("\d+", "".join(tup))
    deviceId = "".join(tupnum)
    return deviceId
