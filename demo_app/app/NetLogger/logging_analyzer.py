'''
logging_analyzer.py

It analyses newly generated cellular event log file,
log it and saves to external storage.

Author: Zengwen Yuan
Version: 3.0
'''

import os
import re
import sys
import subprocess
import datetime
import shutil

from mobile_insight.analyzer import Analyzer

ANDROID_SHELL = "/system/bin/sh"

__all__ = ['LoggingAnalyzer']

class LoggingAnalyzer(Analyzer):
    """
    An ananlyzer for cellular events logging and decoding
    """

    def __init__(self):
        Analyzer.__init__(self)

        self.__logdir            = "/sdcard/mobileinsight/log/"
        self.__original_filename = ""

        if not os.path.exists(self.__logdir):
            os.makedirs(self.__logdir)

        self.add_source_callback(self._logger_filter)


    def _logger_filter(self, msg):
        """
        Callback to process new generated logs.

        :param msg: the message from trace collector.
        :type msg: Event
        """
        if msg.type_id.find("new_diag_log") != -1:
            self.__log_timestamp     = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.__original_filename = msg.data
            # chmodcmd = "chmod 644 " + self.__original_filename
            # proc = subprocess.Popen(chmodcmd, executable = ANDROID_SHELL, shell = True)
            # proc.wait()
            self._save_log()


    def _save_log(self):
        orig_basename  = os.path.basename(self.__original_filename)
        orig_dirname   = os.path.dirname(self.__original_filename)
        milog_basename = "milog_" + self.__log_timestamp + '_' + self.__get_phone_info() + '.mi2log'
        milog_absname  = os.path.join(self.__logdir, milog_basename)

        print "MobileInsight (NetLogger): original filename = " + self.__original_filename
        print "MobileInsight (NetLogger): uploadfileabsname = " + uploadfileabsname

        shutil.copyfile(self.__original_filename, milog_fileabsname)
        try:
            os.remove(self.__original_filename)
        except:
            pass

        # return milog_absname


    def _get_phone_info(self):
        cmd = "getprop"
        modelFound        = False
        manufacturerFound = False
        operatorFound     = False
        serialnoFound     = False
        proc = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
        for line in proc.stdout:
            if "[ro.product.model]" in line:
                model = re.findall('\[(.*?)\]', line)[1]
                modelFound = True
                continue
            if "[ro.product.manufacturer]" in line:
                manufacturer = re.findall('\[(.*?)\]', line)[1]
                manufacturerFound = True
                continue
            if "[gsm.operator.alpha]" in line:
                operator = re.findall('\[(.*?)\]', line)[1]
                operatorFound = True
                continue
            if "[ro.serialno]" in line:
                serialno = re.findall('\[(.*?)\]', line)[1]
                serialnoFound = True
                continue
            if modelFound and manufacturerFound and operatorFound:
                proc.kill()
                break
        proc.wait()

        if operator == "":
            operator = "null"

        if serialnoFound is True:
            return serialno + '_' + manufacturer + '-' + model + '_' + operator
        else:
            return self._get_device_id() + '_' + manufacturer + '-' + model + '_' + operator


    def _get_device_id(self):
        cmd = "service call iphonesubinfo 1"
        self._run_shell_cmd(cmd)
        out = proc.communicate()[0]
        tup = re.findall("\'.+\'", out)
        tupnum = re.findall("\d+", "".join(tup))
        deviceId = "".join(tupnum)
        return deviceId
