import mi2app_utils

import os
import sys
import threading
import time
import traceback

from kivy.config import ConfigParser


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
    print arg,app_dir,os.path.join(app_dir, arg)

    namespace = {"service_context": mi2app_utils.get_service_context()}

    #Load configurations as global variables
    config = ConfigParser()
    config.read('/sdcard/.mobileinsight.ini')

    ii = arg.rfind('/')
    section_name = arg[ii+1:]
    config_options = config.options(section_name)

    plugin_config={}
    for item in config_options:
        plugin_config[item] = config.get(section_name, item)

    namespace["plugin_config"] = plugin_config

    execfile(app_file, namespace)
