#!/usr/bin/python
# Filename: plmn_monitor.py


"""
A background monitor to get all necessary information for the decision

Author: Yuanjie Li
"""

from bplmn_search import *

import thread
import os

class PlmnMonitor:

    # TODO: run decision fault check and prevent unecessary switch
    
    def __init__(self, at_serial_port):
        self.bplmn = BplmnSearch(at_serial_port)

    def _run_shell_cmd(self, cmd):
        """
            Run an adb shell command (as root)

            :param cmd: the command to be executed
            :returns: the results of the command
        """
        return os.popen(cmd).readlines()

    def get_current_location(self):
        """
            Return the last known GPS location

            :returns: a (latitude,longitude) pair
        """
        res = self._run_shell_cmd("\"su -c dumpsys location | grep 'passive: Location'\"")
        last_known_item = res[-1]
        last_known_list = last_known_item.split(' ')
        last_known_gps = last_known_list[6].split(',')

        # print "GPS location:",last_known_gps
        return (float(last_known_gps[0]),float(last_known_gps[1]))

    def run(self):
        # should pass the param msg?
        thread.start_new_thread(self.bplmn.run,(msg))
