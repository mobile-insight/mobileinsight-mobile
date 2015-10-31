"""
mi2app_utils.py

Define utility variables and functions for apps.
"""

__all__ = [ "get_service_context",
            "get_cache_dir",
            "get_files_dir",
            ]

from jnius import autoclass

service_context = autoclass('org.renpy.android.PythonService').mService

def get_service_context():
    return service_context

def get_cache_dir():
    return str(service_context.getCacheDir().getAbsolutePath())

def get_files_dir():
    return str(service_context.getFilesDir().getAbsolutePath())
