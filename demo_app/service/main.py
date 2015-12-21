import mi2app_utils

import os
import sys
import threading
import time
import traceback


def alive_worker(secs):
    while True:
        # print "I'm still alive..."
        time.sleep(secs)

if __name__ == "__main__":
    # get the argument passed
    arg = os.getenv("PYTHON_SERVICE_ARGUMENT")

    try:
        t = threading.Thread(target=alive_worker, args=(30.0,))
        t.start()

        APP_DIR = os.path.join(mi2app_utils.get_files_dir(), "app")
        sys.path.append(os.path.join(APP_DIR, arg)) # add this dir to module search path
        app_file = os.path.join(APP_DIR, arg, "main.mi2app")
        print "Phone model: " + mi2app_utils.get_phone_model()
        print "Running app: " + app_file
        namespace = {"service_context": mi2app_utils.get_service_context()}
        execfile(app_file, namespace)
    except:
        print str(traceback.format_exc())
