#!/usr/bin/python
# Filename: at-cmd.py

"""

An interface for AT commands

Author: Yuanjie Li

"""

import sys
import subprocess
import codecs

ANDROID_SHELL = "/system/bin/sh"

class AtCmd(object):
    

    def __init__(self,at_device):

        '''
        Initialize the at command interface. Disable the echo mode

        :param at_device: the serial port name for AT command
        :types at_device: string
        '''

        # self._run_shell_cmd("su -c chown root "+at_device,True)
        # self._run_shell_cmd("su -c chgrp sdcard_rw "+at_device,True)
        # self._run_shell_cmd("su -c chmod 777 "+at_device,True)

        # self.phy_ser = open(at_device,"rw")
        self.at_device = at_device

        at_res_cmd = "su -c cat "+at_device+">/sdcard/at_tmp.txt"
        self.at_proc = subprocess.Popen(at_res_cmd, executable=ANDROID_SHELL, shell=True)

        #disable echo mode
        self.run_at_cmd("ATE0")

    def _run_shell_cmd(self, cmd, wait=False):
        p = subprocess.Popen(cmd, executable=ANDROID_SHELL, shell=True)
        if wait:
            p.wait()
            return p.returncode
        else:
            return None


    def run_at_cmd(self,cmd):
        '''
        Send an AT command, return responses

        :param cmd: the command to be sent
        :returns: the return value of command
        '''
        full_cmd = 'su -c \"echo -e \'' + cmd + '\\r\\n\' > ' + self.at_device+"\""
        p = subprocess.Popen(full_cmd, executable=ANDROID_SHELL, shell=True)
        p.wait()
        
        res=""
        with codecs.open('/sdcard/at_tmp.txt',encoding='utf8') as fp:
        	while True:
        	    s = fp.read()
        	    res+=s
        	    if len(res)>2 and res[-2]=="\r" and res[-1]=="\n":
        	    	break
        return res

if __name__=="__main__":
    at_cmd = AtCmd("/dev/smd11")
    at_cmd.run_at_cmd("ATD3106148922")

