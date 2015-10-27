from jnius import autoclass

import os
import time
import traceback

ServiceContext = autoclass('org.renpy.android.PythonService').mService

# get the argument passed
arg = os.getenv("PYTHON_SERVICE_ARGUMENT")

def get_files_dir():
    return str(ServiceContext.getFilesDir().getAbsolutePath())

if __name__ == "__main__":
    try:
        APP_DIR = os.path.join(get_files_dir(), "app")
        app_file = os.path.join(APP_DIR, arg, "main.mi2app")
        print "Running app: " + app_file
        namespace = {"service_context": ServiceContext}
        execfile(app_file, namespace)
    except:
        print str(traceback.format_exc())
