#!/usr/bin/python
# Filename: at_cmd.py

"""

An interface for AT commands

Author: Yuanjie Li

"""

import sys
import subprocess
import codecs

ANDROID_SHELL = "/system/bin/sh"
at_log_file = "/sdcard/at_tmp.txt"

class AtCmd(object):
    
    def __init__(self, at_device):

        '''
        Initialize the at command interface. Disable the echo mode

        :param at_device: the serial port name for AT command
        :types at_device: string
        '''

        # self._run_shell_cmd("su -c chown root "+at_device,True)
        # self._run_shell_cmd("su -c chgrp sdcard_rw "+at_device,True)
        self._run_shell_cmd("su -c chmod 777 " + at_device, True)

        # self.phy_ser = open(at_device,"rw")
        self.at_device = at_device

        at_res_cmd = "su -c cat " + at_device + ">" + at_log_file
        self.at_proc = subprocess.Popen(at_res_cmd, executable = ANDROID_SHELL, shell = True)

        self.cmd_count = 0

        #disable echo mode
        self.run_cmd("ATE0")

    def _run_shell_cmd(self, cmd, wait = False):
        p = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True)
        if wait:
            p.wait()
            return p.returncode
        else:
            return None


    def run_cmd(self, cmd):
        '''
        Send an AT command, return responses

        :param cmd: the command to be sent
        :returns: the return value of AT command
        '''
        full_cmd = 'su -c \"echo -e \'' + cmd + '\\r\\n\' > ' + self.at_device + "\""
        p = subprocess.Popen(full_cmd, executable = ANDROID_SHELL, shell = True)
        p.wait()
        
        while True:
            res = ""
            count = 0
            with codecs.open(at_log_file, encoding = 'utf8') as fp:
                while True:
                    s = fp.readline()
                    if not s:
                    	break
                    res += s
                    if len(res) > 2 and res[-2] == "\r" and res[-1] == "\n":
                        if count == self.cmd_count:
                            break
                        else:
                        	count = count + 1
                        	res = ""
            if res:
            	self.cmd_count = self.cmd_count + 1
                return res

if __name__=="__main__":
    # at_cmd = AtCmd("/dev/smd11")
    at_cmd = AtCmd(at_device)
    print at_cmd.run_cmd("ATD3106148922")
