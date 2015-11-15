"""
RealtimeAnalyzer

Author: Jiayao Li
"""

import mobile_insight
from mobile_insight.analyzer import Analyzer
from mobile_insight.monitor.dm_collector import DMLogPacket
import mi2app_utils

from datetime import datetime
import os
import threading
import time
import timeit


__all__ = ["RealtimeAnalyzer"]


def flight_mode_worker(states):
    """
    Controling switching flight mode.

    Shell cmds are taken from http://stackoverflow.com/questions/13766909 .
    """
    in_flight_mode = False
    while True:
        if in_flight_mode:
            print "Exit flight mode"
            with states["lock"]:
                cmd = "su -c settings put global airplane_mode_on 0"
                cmd += " && "
                cmd += "su -c am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false"
                mi2app_utils.run_shell_cmd(cmd)
                ts = timeit.default_timer()
                mi2app_utils.run_shell_cmd("")
                states["exit_flight_mode_timestamp"] = ts
                states["first_msg_received"] = False
            in_flight_mode = False
            time.sleep(10)
        else:
            print "Enter flight mode"
            # open flight mode
            cmd = "su -c settings put global airplane_mode_on 1"
            cmd += " && "
            cmd += "su -c am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true"
            mi2app_utils.run_shell_cmd(cmd)
            in_flight_mode = True
            time.sleep(30)


class RealtimeAnalyzer(Analyzer):
    """
    Test the latency of messages
    """
    
    def __init__(self):
        Analyzer.__init__(self)

        self.add_source_callback(self._callback)
        self._reference_ts_android = None
        self._reference_ts_dm = None
        self._i = 0

        self._run_flight_mode_test = False
        self._thread_running = False
        self._t = None
        self._fmtest_states = None

        self._latency = []

    def enable_flight_mode_test(self):
        self._run_flight_mode_test = True
        self._fmtest_states = dict()
        self._fmtest_states["lock"] = threading.Lock()
        self._fmtest_states["exit_flight_mode_timestamp"] = None
        self._fmtest_states["first_msg_received"] = True

        self._t = threading.Thread( target=flight_mode_worker,
                                    args=(self._fmtest_states,))
        self._thread_running = False

    def calibrate_timestamp(self):
        if self._reference_ts_android is None:
            self._reference_ts_android, self._reference_ts_dm = self._calibrate_timestamp()
            print "First Android timestamp:", self._reference_ts_android
            with open(self._get_lantency_log_filename(), "w") as fd:
                pass

    def _get_lantency_log_filename(self):
        return os.path.join(mi2app_utils.get_cache_dir(), "latency.txt")

    def _calibrate_timestamp(self):
        script = """echo -e 'AT+CCLK="11/11/11,00:00:00"\\r\\n' > /dev/smd0"""
        script_filename = os.path.join(mi2app_utils.get_cache_dir(), "calibrate_timestamp.sh")
        with open(script_filename, "w") as fd:
            fd.write(script + "\n")

        ts = timeit.default_timer()
        mi2app_utils.run_shell_cmd("su -c sh %s" % script_filename, wait=True)
        ret_ts1 = timeit.default_timer()
        print "Shell exec time: %f" % (ret_ts1 - ts)
        ret_ts2 = datetime(2011, 11, 11, 0, 0, 0)
        return (ret_ts1, ret_ts2)

    def _callback(self, msg):
        if self._run_flight_mode_test and not self._thread_running:
            print "Start flight mode thread"
            self._t.start()
            self._thread_running = True

        if msg.type_id == "new_qmdl_file":
            print "End of %s" % msg.data
            self._latency.append( (-666.0, -666.0, -666.0, msg.type_id) )

        else:
            log_item = msg.data.decode()

            if self._run_flight_mode_test:
                with self._fmtest_states["lock"]:
                    if not self._fmtest_states["first_msg_received"]:
                        ts = self._fmtest_states["exit_flight_mode_timestamp"]
                        latency1 = msg.timestamp - ts
                        latency2 = timeit.default_timer() - ts
                        print "Latency:", latency1, latency2
                        self._fmtest_states["first_msg_received"] = True

            delta1 = msg.timestamp - self._reference_ts_android
            delta2 = (log_item["timestamp"] - self._reference_ts_dm).total_seconds()
            self._latency.append( (delta1, delta2, delta1 - delta2, msg.type_id) )

            if (self._i % 1) == 0:
                print delta1, delta2, delta1 - delta2, msg.type_id
                with open(self._get_lantency_log_filename(), "a") as fd:
                    for tup in self._latency:
                        fd.write("%.5f %.5f %.5f %s\n" % tup)
                self._latency = []
                # print (datetime.utcnow() - log_item["timestamp"]).total_seconds(), self.source.get_avg_read_latency()
            self._i += 1
