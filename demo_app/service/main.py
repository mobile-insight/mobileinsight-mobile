import mi2app_utils

import os
import sys
import time
import traceback


# get the argument passed
arg = os.getenv("PYTHON_SERVICE_ARGUMENT")

if __name__ == "__main__":
    try:
        APP_DIR = os.path.join(mi2app_utils.get_files_dir(), "app")
        sys.path.append(os.path.join(APP_DIR, arg)) # add this dir to module search path
        app_file = os.path.join(APP_DIR, arg, "main.mi2app")
        print "Running app: " + app_file
        namespace = {"service_context": mi2app_utils.get_service_context()}
        execfile(app_file, namespace)
    except:
        print str(traceback.format_exc())
