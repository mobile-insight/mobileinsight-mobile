import android
import threading
from time import sleep
from kivy.lib.osc import oscAPI as osc
from kivy.utils import platform
import traceback
from kivy.clock import Clock
from kivy.logger import Logger



class OSCConfig:
    # event addr used to send/recv event data
    event_addr = '/event'
    # control addr used to control monitor/analyzer lifecycle
    control_addr = '/control'
    service_port = 3000
    app_port = 3001
    # app side oscid
    oscid = None

def setup_osc():
    osc.init()
    OSCConfig.oscid = osc.listen(port=OSCConfig.app_port)
    Clock.schedule_interval(lambda *x: osc.readQueue(thread_id=OSCConfig.oscid), .5)
    Logger.info('coordinator: setup osc at ' + str(OSCConfig.app_port))
    Logger.info('coordinator: osc id: ' + OSCConfig.oscid)

def stop_osc():
    osc.dontListen()

def setup_service():
    android.start_service(title='MobileInsight',
                          description='MobileInsight plugins have stopped.',
                          arg='')
    Logger.info('coordinator: start background service')

def stop_service():
    android.stop_service()
    Logger.info('coordinator: stop background service')


class Coordinator(object):
    '''App side control center
    see control for detailed protocol
    '''
    def __init__(self):
        self._analyzers = []
        self._screen_callbacks = []
        self._service_ready = threading.Event()

    def register_analyzer(self, analyzer):
        self._analyzers.append(analyzer)

    def register_callback(self, callback):
        self._screen_callbacks.append(callback)

    def start(self):
        '''
        Start service to setup monitor, analyzers,
        use osc to listen for data update
        '''
        setup_osc()
        setup_service()
        osc.bind(OSCConfig.oscid, self.event_callback, OSCConfig.event_addr)
        Logger.info('coordinator: coordinator bind to ' + OSCConfig.event_addr)
        osc.bind(OSCConfig.oscid, self.control_callback, OSCConfig.control_addr)
        Logger.info('coordinator: coordinator bind to ' + OSCConfig.control_addr)
        listen_thread = threading.Thread(target=self.listen_osc, args=(OSCConfig.oscid,))
        listen_thread.start()
        Logger.info('coordinator: ' + 'listen thread starts')

    def setup_analyzers(self):
        argstr = ','.join(self._analyzers)
        self.send_control(argstr)

    def listen_osc(self, oscid):
        while True:
            osc.readQueue(thread_id=oscid)
            sleep(.5)

    def event_callback(self, message, *args):
        Logger.info('coordinator <RECV: event msg: ' + message[2])
        def G(f): return f(message[2])
        map(G, self._screen_callbacks)

    def control_callback(self, message, *args):
        # set the Event lock once service is ready
        Logger.info('coordinator <RECV: control msg: ' + message[2])
        self._service_ready.set()

    def send_control(self, message):
        def thread_target(msg):
            # wait for service ready event
            self._service_ready.wait()
            osc.sendMsg(OSCConfig.control_addr, dataArray=[str(msg),], port=OSCConfig.service_port)
            Logger.info('coordinator SEND>: control msg: ' + msg)
        send_thread = threading.Thread(target=thread_target, args=(message,))
        send_thread.start()

    def stop(self):
        Logger.info('coordinator: ' + '// stops does nothing right now')

# only create a singleton coordinator for app
# should always import this coordinator
COORDINATOR = Coordinator()
Logger.info('coordinator: created COORDINATOR')
