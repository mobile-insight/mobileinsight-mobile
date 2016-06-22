"""
mi2app_utils.py

Define utility variables and functions for apps.
"""

__all__ = [ "get_service_context",
            "get_cache_dir",
            "get_files_dir",
            "get_phone_manufacturer",
            "get_phone_model",
            "run_shell_cmd",
            "File",
            "FileOutputStream"
            ]

from jnius import autoclass
# FIXME(likayo): subprocess module in Python 2.7 is not thread-safe. Use subprocess32 instead.
import subprocess

service_context = autoclass('org.renpy.android.PythonService').mService
android_os_build = autoclass("android.os.Build")
File = autoclass("java.io.File")
FileOutputStream = autoclass('java.io.FileOutputStream')

def get_service_context():
    return service_context

def get_cache_dir():
    return str(service_context.getCacheDir().getAbsolutePath())

def get_files_dir():
    return str(service_context.getFilesDir().getAbsolutePath())


def get_phone_manufacturer():
    return android_os_build.MANUFACTURER

def get_phone_model():
    return android_os_build.MODEL

def run_shell_cmd(cmd, wait=False):
    ANDROID_SHELL = "/system/bin/sh"
    p = subprocess.Popen(cmd, executable=ANDROID_SHELL, shell=True)
    if wait:
        p.wait()
