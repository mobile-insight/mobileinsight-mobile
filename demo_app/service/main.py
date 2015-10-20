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
        app_file = os.path.join(get_files_dir(), "res", arg + ".mi2app")
        print "Running app: " + app_file
        execfile(app_file)
    except:
        print str(traceback.format_exc())
