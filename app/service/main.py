import os
import sys
import threading
import time
import logging
import traceback
import datetime as dt
import signal
from kivy.logger import Logger
from kivy.config import ConfigParser
from kivy.lib.osc import oscAPI as osc
from service.control import Control, OSCConfig
from service import mi2app_utils
from service import GpsListener
import kivy
kivy.require('1.4.0')

reload(sys)
sys.setdefaultencoding('utf8')


def receive_signal(signum, stack):
    print 'Received:', signum

class MyFormatter(logging.Formatter):
    converter = dt.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            # t = ct.strftime("%Y-%m-%d %H:%M:%S")
            # s = "%s,%03d" % (t, record.msecs)
            s = ct.strftime(" ")
        return s


def setup_logger(app_name):
    '''Setup the analyzer logger.

    NOTE: All analyzers share the same logger.

    :param level: the loggoing level. The default value is logging.INFO.
    '''
    level = logging.INFO

    config = ConfigParser()
    config.read('/sdcard/.mobileinsight.ini')
    if config.has_option('mi_general', 'log_level'):
        level_config = config.get('mi_general', 'log_level')
        if level_config == "info":
            level = logging.INFO
        elif level_config == "debug":
            level = logging.DEBUG
        elif level_config == "warning":
            level = logging.WARNING
        elif level_config == "error":
            level = logging.ERROR
        elif level_config == "critical":
            level = logging.CRITICAL

    l = logging.getLogger("mobileinsight_logger")
    if len(l.handlers) < 1:
        # formatter = MyFormatter(
        #     '%(asctime)s %(message)s',
        #     datefmt='%Y-%m-%d,%H:%M:%S.%f')
        formatter = MyFormatter('%(message)s')
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)

        l.setLevel(level)
        l.addHandler(streamHandler)
        l.propagate = False

        log_file = os.path.join(
            mi2app_utils.get_mobileinsight_analysis_path(),
            app_name + "_log.txt")
        Logger.info('service: mi log file: ' + log_file)

        fileHandler = logging.FileHandler(log_file, mode='w')
        fileHandler.setFormatter(formatter)
        l.addHandler(fileHandler)
        l.disabled = False


def on_gps(provider, eventname, *args):
    if eventname == 'provider-disabled':
        pass
    elif eventname == 'location':
        location = args[0]
        Logger.info('gps: ' + str(location.getLatitude()) + str(location.getLongitude()))


def exec_legacy(arg):
    try:
        tmp = arg.split(":")
        if len(tmp) < 2:
            raise AssertionError("Error: incorrect service path: " + arg)
        app_name = tmp[0]
        app_path = tmp[1]

        # print "Service: app_name=",app_name," app_path=",app_path
        setup_logger(app_name)

        t = threading.Thread(target=alive_worker, args=(30.0,))
        t.start()

        app_dir = os.path.join(mi2app_utils.get_files_dir(), "app")
        # add this dir to module search path
        sys.path.append(os.path.join(app_dir, app_path))
        app_file = os.path.join(app_dir, app_path, "main.mi2app")
        Logger.info("Phone model: " + mi2app_utils.get_phone_model())
        Logger.info("Running app: " + app_file)
        # print arg,app_dir,os.path.join(app_dir, arg)

        namespace = {"service_context": mi2app_utils.get_service_context()}

        # Load configurations as global variables
        config = ConfigParser()
        config.read('/sdcard/.mobileinsight.ini')

        ii = arg.rfind('/')
        section_name = arg[ii + 1:]

        plugin_config = {}
        if section_name in config.sections():
            config_options = config.options(section_name)
            for item in config_options:
                plugin_config[item] = config.get(section_name, item)

        namespace["plugin_config"] = plugin_config

        gps_provider = GpsListener(on_gps)
        gps_provider.start()

        execfile(app_file, namespace)

        # print app_name, "stops normally"

    except Exception as e:
        # Print traceback logs to analysis
        tb_exc = traceback.format_exc()
        Logger.error(tb_exc)
        l = logging.getLogger("mobileinsight_logger")
        l.error(tb_exc)
        sys.exit(tb_exc)

def alive_worker(secs):
    """
    Keep service alive
    """
    while True:
        Logger.info('service: ' + 'alive thread wakes')
        time.sleep(secs)

def setup_service():
    Logger.info('service: setup_service')
    setup_logger('mi')

    # add this dir to module search path
    app_dir = os.path.join(mi2app_utils.get_files_dir(), "app")
    sys.path.append(os.path.join(app_dir, 'service'))
    Logger.info('service: sys path added: ' + str(sys.path))

    # setup control and listen to osc signal
    control = Control()
    Logger.info('service: control created' + repr(control))

    osc.init()
    OSCID = osc.listen(port=OSCConfig.service_port)
    # def dummy_callback(msg, *args):
    #     Logger.info('service: dummy callback: ' + str(msg))
    # osc.bind(OSCID, dummy_callback, OSCConfig.control_addr)
    osc.bind(OSCID, control.osc_callback, OSCConfig.control_addr)
    Logger.info('service: osc setup, id: ' + OSCID)

    gps_provider = GpsListener(on_gps)
    gps_provider.start()

    osc.sendMsg(OSCConfig.control_addr, dataArray=['service ready',], port=OSCConfig.app_port)
    Logger.info('service SEND>: service ready msg sent')
    while True:
        osc.readQueue(thread_id=OSCID)
        time.sleep(.5)

if __name__ == "__main__":
    Logger.info('service: start service')
    signal.signal(signal.SIGINT, receive_signal)

    arg = os.getenv("PYTHON_SERVICE_ARGUMENT")  # get the argument passed

    if arg is None:
        Logger.error('No service arguments found')
    elif ':' in arg:
        exec_legacy(arg)
    else:
        setup_service()
