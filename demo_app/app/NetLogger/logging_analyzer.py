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
import signal

from mobile_insight.analyzer import Analyzer

ANDROID_SHELL = "/system/bin/sh"

__all__ = ['LoggingAnalyzer']

class LoggingAnalyzer(Analyzer):
    """
    An ananlyzer for cellular events logging and decoding
    """

    def __init__(self):
        Analyzer.__init__(self)

        self.__logdir            = "/sdcard/mobile_insight/log/"
        self.__txtlogdir         = "/sdcard/mobile_insight/log/decoded"
        self.__original_filename = ""
        self.__decodemsg         = []
        self.__msg_cnt           = 0
        self.__decode_cnt        = 0
        self.__txt_log_name = "mi2log_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
        self.__txt_log_path = os.path.join(self.__txtlogdir, self.__txt_log_name)

        if not os.path.exists(self.__logdir):
            os.makedirs(self.__logdir)
        if not os.path.exists(self.__txtlogdir):
            os.makedirs(self.__txtlogdir)

        self.add_source_callback(self._logger_filter)


    def _logger_filter(self, msg):
        """
        Callback to process new generated logs.

        :param msg: the message from trace collector.
        :type msg: Event
        """
        # save mi2log
        if msg.type_id.find("new_diag_log") != -1:
            # print "MobileInsight (NetLogger): oh new mi2log save!"
            self.__log_timestamp     = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.__original_filename = msg.data
            self._save_log()

        # save decoded txt
        if (msg.type_id.startswith("LTE_") or msg.type_id.startswith("WCDMA_") or msg.type_id.startswith("UMTS_")):
            # print "MobileInsight (NetLogger): oh yeah new msg!"
            
            try:
                log_item      = msg.data.decode()
                log_item_dict = dict(log_item)
                if not log_item_dict.has_key('Msg'):
                    return

                self.__decodemsg.append("type_id: %s\n" % str(log_item_dict["type_id"]))
                self.__decodemsg.append("timestamp: %s GMT\n" % str(log_item_dict["timestamp"]))
                self.__decodemsg.append(log_item_dict['Msg'])
                self.__msg_cnt += 1
                self.__decode_cnt += 1
            except:
                pass

            if self.__decode_cnt >= 20:
                with open(self.__txt_log_path, 'a') as f:
                    f.writelines(self.__decodemsg)
                self.__decodemsg         = []
                self.__decode_cnt        = 0
                # print "MobileInsight (NetLogger): txt log saved"

            if self.__msg_cnt >= 200:  # open a new file
                self.__txt_log_name      = "mi2log_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
                self.__txt_log_path = os.path.join(self.__txtlogdir, self.__txt_log_name)
                print "save path is " + self.__txt_log_path
                self.__decodemsg         = []
                self.__msg_cnt           = 0
                self.__decode_cnt        = 0
                # print "MobileInsight (NetLogger): new txt log saved"


    def _save_log(self):
        orig_basename  = os.path.basename(self.__original_filename)
        orig_dirname   = os.path.dirname(self.__original_filename)
        milog_basename = "milog_" + self.__log_timestamp + '_' + self.__get_phone_info() + '.mi2log'
        milog_absname  = os.path.join(self.__logdir, milog_basename)
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
