import mi2app_utils

import os
import sys
import threading
import time
import traceback
import logging
import datetime as dt

from kivy.config import ConfigParser


def alive_worker(secs):
    while True:
        time.sleep(secs)

class MyFormatter(logging.Formatter):
    converter=dt.datetime.fromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s

def setup_logger(level=logging.INFO):
    '''Setup the analyzer logger.

    NOTE: All analyzers share the same logger.

    :param level: the loggoing level. The default value is logging.INFO.
    '''

    l = logging.getLogger("mobileinsight_logger")
    if len(l.handlers)<1:
        # formatter = MyFormatter('%(asctime)s %(message)s',datefmt='%Y-%m-%d,%H:%M:%S.%f')
        formatter = MyFormatter('%(message)s')
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)

        l.setLevel(level)
        l.addHandler(streamHandler)
        l.propagate = False


        log_file = os.path.join(mi2app_utils.get_mobile_insight_path(),"log.txt")

        fileHandler = logging.FileHandler(log_file, mode='w')
        fileHandler.setFormatter(formatter)
        l.addHandler(fileHandler)  
        l.disabled = False

if __name__ == "__main__":

    try:
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
        
        plugin_config={}
        if section_name in config.sections():
            config_options = config.options(section_name)
            for item in config_options:
                plugin_config[item] = config.get(section_name, item)

        namespace["plugin_config"] = plugin_config


        setup_logger()

        execfile(app_file, namespace)

    except Exception, e:
        import traceback
        sys.exit(str(traceback.format_exc()))
