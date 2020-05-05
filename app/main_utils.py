"""
main_utils.py

Define utility variables and functions for apps.
"""
import jnius
from jnius import autoclass, cast
import android

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
# from kivy.lib.osc import oscAPI as osc
from kivy.logger import Logger


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
    Logger.info('Running cmd: {}'.format(cmd))
    res, err = p.communicate((cmd + '\n').encode())

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
    if res.startswith(b"mt"):
        return ChipsetType.MTK
    elif res.startswith(b"msm") or res.startswith(b"mdm") or res.startswith(b"sdm"):
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
    return str(current_activity.getFilesDir().getAbsolutePath() + '/app')

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
    # return telephonyManager.getNetworkOperatorName()+"-"+telephonyManager.getNetworkOperator()
    return telephonyManager.getNetworkOperator()


def get_device_id():
    cmd = "service call iphonesubinfo 1"
    out = run_shell_cmd(cmd)
    tup = re.findall("\'.+\'", out)
    tupnum = re.findall("\d+", "".join(tup))
    deviceId = "".join(tupnum)
    return deviceId


def init_libs():
    """
    Initialize libs required by MobileInsight.
    It creates sym links to libs, and chmod of critical execs
    """

    if not is_rooted():
        Logger.error(
            "MobileInsight requires root privilege. \
            Please root your device for correct functioning.")


    libs_path = os.path.join(get_files_dir(), "data")
    cmd = ""

    libs_mapping = {
        "libwireshark.so": [
            "libwireshark.so.6", "libwireshark.so.6.0.1"], "libwiretap.so": [
            "libwiretap.so.5", "libwiretap.so.5.0.1"], "libwsutil.so": [
            "libwsutil.so.6", "libwsutil.so.6.0.0"]}
    for lib in libs_mapping:
        for sym_lib in libs_mapping[lib]:
            # if not os.path.isfile(os.path.join(libs_path,sym_lib)):
            if True:
                # TODO: chown to restore ownership for the symlinks
                cmd = cmd + " ln -s " + \
                    os.path.join(libs_path, lib) + " " + os.path.join(libs_path, sym_lib) + "; "

    exes = ["diag_revealer",
            "diag_revealer_mtk",
            "android_pie_ws_dissector",
            "android_ws_dissector"]
    for exe in exes:
        cmd = cmd + " chmod 755 " + os.path.join(libs_path, exe) + "; "

    cmd = cmd + "chmod -R 755 " + libs_path
    Logger.info('init libs: {}'.format(cmd))
    run_shell_cmd(cmd)


def check_security_policy():
    """
    Update SELinux policy.
    For Nexus 6/6P, the SELinux policy may forbids the log collection.
    """

    cmd = "setenforce 0; "

    cmd = cmd + "supolicy --live \"allow init logd dir getattr\";"

    # # Depreciated supolicies. Still keep them for backup purpose
    cmd = cmd + "supolicy --live \"allow init init process execmem\";"
    cmd = cmd + \
        "supolicy --live \"allow atfwd diag_device chr_file {read write open ioctl}\";"
    cmd = cmd + "supolicy --live \"allow init properties_device file execute\";"
    cmd = cmd + \
        "supolicy --live \"allow system_server diag_device chr_file {read write}\";"

    # # Suspicious supolicies: MI works without them, but it seems that they SHOULD be enabled...

    # # mi2log permission denied (logcat | grep denied), but no impact on log collection/analysis
    cmd = cmd + \
        "supolicy --live \"allow untrusted_app app_data_file file {rename}\";"

    # # Suspicious: why still works after disabling this command? Won't FIFO fail?
    cmd = cmd + \
        "supolicy --live \"allow init app_data_file fifo_file {write open getattr}\";"
    cmd = cmd + \
        "supolicy --live \"allow init diag_device chr_file {getattr write ioctl}\"; "

    # Nexus 6 only
    cmd = cmd + \
        "supolicy --live \"allow untrusted_app diag_device chr_file {write open getattr}\";"
    cmd = cmd + \
        "supolicy --live \"allow system_server diag_device chr_file {read write}\";"
    cmd = cmd + \
        "supolicy --live \"allow netmgrd diag_device chr_file {read write}\";"
    cmd = cmd + \
        "supolicy --live \"allow rild diag_device chr_file {read write}\";"
    cmd = cmd + \
        "supolicy --live \"allow rild debuggerd app_data_file {read open getattr}\";"
    cmd = cmd + \
        "supolicy --live \"allow debuggerd app_data_file file {read open getattr}\";"
    cmd = cmd + \
        "supolicy --live \"allow zygote zygote process {execmem}\";"
    cmd = cmd + \
        "supolicy --live \"allow zygote ashmem_device chr_file {execute}\";"
    cmd = cmd + \
        "supolicy --live \"allow zygote zygote_tmpfs file {execute}\";"
    cmd = cmd + \
        "supolicy --live \"allow zygote activity_service service_manager {find}\";"
    cmd = cmd + \
        "supolicy --live \"allow zygote package_service service_manager {find}\";"
    cmd = cmd + \
        "supolicy --live \"allow zygote system_server binder {call}\";"
    cmd = cmd + \
        "supolicy --live \"allow zygote system_server binder {transfer}\";"
    cmd = cmd + \
        "supolicy --live \"allow system_server zygote binder {call}\";"
    cmd = cmd + \
        "supolicy --live \"allow untrusted_app sysfs file {read open getattr}\";"

    cmd = cmd + \
        "supolicy --live \"allow wcnss_service mnt_user_file dir {search}\";"

    cmd = cmd + \
        "supolicy --live \"allow wcnss_service fuse dir {read open search}\";"

    cmd = cmd + \
        "supolicy --live \"allow wcnss_service mnt_user_file lnk_file {read}\";"

    cmd = cmd + \
        "supolicy --live \"allow wcnss_service fuse file {read append getattr}\";"

    # MI phones

    cmd = cmd + \
        "supolicy --live \"allow untrusted_app_25 diag_device chr_file {open read write getattr}\";"

    cmd = cmd + \
        "supolicy --live \"allow crash_dump app_data_file file {open getattr read write search}\";"

    cmd = cmd + \
        "supolicy --live \"allow zygote cgroup file {create}\";"

    cmd = cmd + \
        "supolicy --live \"allow crash_dump app_data_file dir {read write search}\";"


    run_shell_cmd(cmd)


def check_diag_mode():
    """Check if diagnostic mode is enabled.
    Note that this function is chipset-specific: Qualcomm and MTK have different detection approaches
    """
    chipset_type = get_chipset_type()
    if chipset_type == ChipsetType.QUALCOMM:
        diag_port = "/dev/diag"
        if not os.path.exists(diag_port):
            return False
        else:
            run_shell_cmd("chmod 777 /dev/diag")
            return True
    elif chipset_type == ChipsetType.MTK:
        cmd = "ps | grep emdlogger1"
        res = run_shell_cmd(cmd)
        if not res:
            return False
        else:
            return True
