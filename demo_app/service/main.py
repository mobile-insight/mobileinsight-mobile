import mi2app_utils

import os
import sys
import threading
import time
import traceback


def alive_worker(secs):
    while True:
        time.sleep(secs)

if __name__ == "__main__":

    arg = os.getenv("PYTHON_SERVICE_ARGUMENT")  # get the argument passed

    t = threading.Thread(target=alive_worker, args=(30.0,))
    t.start()

    app_dir = os.path.join(mi2app_utils.get_files_dir(), "app")
    sys.path.append(os.path.join(app_dir, arg)) # add this dir to module search path
    app_file = os.path.join(app_dir, arg, "main.mi2app")
    print "Phone model: " + mi2app_utils.get_phone_model()
    print "Running app: " + app_file
    namespace = {"service_context": mi2app_utils.get_service_context()}
    execfile(app_file, namespace)
