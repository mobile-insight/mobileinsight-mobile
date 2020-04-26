from kivy.logger import Logger
from kivy.lib.osc import oscAPI as osc
from mobile_insight import monitor, analyzer
from mi2app_utils import get_cache_dir
import os
import threading
import traceback


class OSCConfig:
    # event addr used to send/recv event data
    event_addr = '/event'
    # control addr used to control monitor/analyzer lifecycle
    control_addr = '/control'
    service_port = 3000
    app_port = 3001


def coord_callback(event, *args):
    # send event data to event address and app port,
    # this will be received by screens' coordinator
    Logger.info('control SEND>: event msg: ' + str(event))
    osc.sendMsg(OSCConfig.event_addr, dataArray=[str(event),], port=OSCConfig.app_port)


class Control(object):
    '''Service side control center
    This module manages the monitor, analyzers for mobile-insight app.
    Callbacks receive osc control signal to perform the actions.
    '''
    def __init__(self):
        Logger.info('control: init control...')
        self.analyzers = {}
        self.callbacks = []
        cache_directory = get_cache_dir()
        Logger.info('control: cache_dir: ' + str(cache_directory))
        log_directory = os.path.join(cache_directory, "mi2log")
        self.monitor = monitor.OnlineMonitor()
        Logger.info('control: monitor created: ' + repr(self.monitor))
        self.monitor.set_log_directory(str(log_directory))
        Logger.info('control: monitor log dir: ' + str(log_directory))
        self.monitor.set_skip_decoding(False)
        self._analyzers_ready = threading.Event()
        # monitor_thread = threading.Thread(target=self.monitor_run)
        # monitor_thread.start()
        # Logger.info('control: monitor thread starts')
        # a = analyzer.LteRrcAnalyzer()
        # a.set_source(self.monitor)
        # Logger.info('control: analyzer set source')
        # self.monitor.run()

    # def monitor_run(self):
    #     self.monitor.run()

    def osc_callback(self, msg, *args):
        '''entrance for control
        START: starts the underlying monitor
        STOP: stops the underlying monitor
        ',' separated analyzers: set the analyzers and register
        '''
        Logger.info('control <RECV: ' + str(msg))
        if (len(msg) < 3):
            Logger.error('no value in control message')
            raise Exception('no value in control message')
        value = msg[2]
        if (value == 'STOP'):
            # TODO: does monitor supports stop?
            Logger.info('control: to STOP')
            self.monitor.stop()
        elif (value == 'START'):
            Logger.info('control: to START')
            self._analyzers_ready.wait()
            self.monitor.run()
        else:
            analyzer_names = [s for s in value.split(',') if s != '']
            Logger.info('control: ' + str(analyzer_names))
            self.set_analyzers(analyzer_names)

    def set_analyzers(self, names):

        # make sure there is monitor running
        if (self.monitor is None):
            raise Exception('Monitor not yet set.')

        # remove all unwanted analyzers
        names = set(names)
        keys = set(self.analyzers.keys())
        # for name in keys - names:
        #     self.monitor.deregister(self.analyzers[name])
        #     del self.analyzers[name]
        # then register all wanted but unregistered analyzers
        try:
            for name in names - keys:
                a = getattr(analyzer, name)()
                a.set_source(self.monitor)
                a.register_coordinator_cb(coord_callback)
                self.analyzers[name] = a
        except AttributeError as error:
            Logger.error('service: Analyzer class not found ' + error)
            Logger.error(traceback.format_exc())
        self._analyzers_ready.set()
        Logger.info('control: set analyzers: ' + str(self.analyzers))

