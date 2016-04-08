'''
logging_analyzer.py

It analyses newly generated cellular event log file,
log and decode them, then save the log to external storage.

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

        self.__logdir            = "/sdcard/mobile_insight/log/"
        self.__txtlogdir         = "/sdcard/mobile_insight/log/decoded"
        self.__phone_info        = self._get_phone_info()
        self.__original_filename = ""
        self.__rawmsg            = {}
        self.__rawmsg_key        = ""
        self.__msg_cnt           = 0
        self.__decodemsg         = []
        self.__txt_log_name      = "mi2log_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
        self.__txt_log_path      = os.path.join(self.__txtlogdir, self.__txt_log_name)

        if not os.path.exists(self.__logdir):
            os.makedirs(self.__logdir)
        if not os.path.exists(self.__txtlogdir):
            os.makedirs(self.__txtlogdir)

        with open(self.__txt_log_path, 'a') as f:
            pass
        print "MobileInsight (NetLogger): decoded cellular log being saved to %s, please check." % self.__txt_log_path

        self.add_source_callback(self._logger_filter)


    def _logger_filter(self, msg):
        """
        Callback to process new generated logs.

        :param msg: the message from trace collector.
        :type msg: Event
        """
        # save mi2log
        if msg.type_id.find("new_diag_log") != -1:
            self.__log_timestamp     = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            tmp = msg.data.decode()
            self.__original_filename = tmp.get("filename")

            chmodcmd = "chmod 644 " + self.__original_filename
            p = subprocess.Popen("su ", executable = ANDROID_SHELL, shell = True, \
                                        stdin = subprocess.PIPE, stdout = subprocess.PIPE)
            p.communicate(chmodcmd + '\n')
            p.wait()
            self._save_log()

        # save decoded txt
        if (msg.type_id.startswith("LTE_") or msg.type_id.startswith("WCDMA_") or msg.type_id.startswith("UMTS_")):
            self.__rawmsg[self.__msg_cnt] = msg.data
            self.__msg_cnt += 1

            if len(self.__rawmsg) >= 20:
                try:
                    with open(self.__txt_log_path, 'a') as f:
                        for key in self.__rawmsg:
                            log_item = self.__rawmsg[key].decode_xml()
                            f.writelines(log_item)
                except:
                    pass

                self.__rawmsg.clear()  # reset the dict

            if self.__msg_cnt >= 200:  # open a new file
                self.__txt_log_name = "mi2log_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
                self.__txt_log_path = os.path.join(self.__txtlogdir, self.__txt_log_name)
                print "MobileInsight (NetLogger): decoded cellular log being saved to %s, please check." % self.__txt_log_path
                self.__rawmsg.clear()  # reset the dict
                self.__msg_cnt = 0


    def _save_log(self):
        orig_basename  = os.path.basename(self.__original_filename)
        orig_dirname   = os.path.dirname(self.__original_filename)
        milog_basename = "diag_log_%s_%s_%s.mi2log" % (self.__log_timestamp, self.__phone_info, self._get_opeartor_info())
        milog_absname  = os.path.join(self.__logdir, milog_basename)
        shutil.copyfile(self.__original_filename, milog_absname)
        try:
            os.remove(self.__original_filename)
        except:
            pass

        # return milog_absname


    def _get_phone_info(self):
        cmd          = "getprop ro.product.model; getprop ro.product.manufacturer;"
        proc         = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
        res          = proc.stdout.read().split('\n')
        model        = res[0].replace(" ", "")
        manufacturer = res[1].replace(" ", "")
        phone_info   = self._get_device_id() + '_' + manufacturer + '-' + model
        # print "_get_phone_info() = " + phone_info
        return phone_info


    def _get_opeartor_info(self):
        cmd          = "getprop gsm.operator.alpha"
        proc         = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
        operator     = proc.stdout.read().split('\n')[0].replace(" ", "")
        if operator == '' or operator is None:
            operator = 'null'
        return operator


    def _get_device_id(self):
        cmd = "service call iphonesubinfo 1"
        proc = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
        out = proc.communicate()[0]
        tup = re.findall("\'.+\'", out)
        tupnum = re.findall("\d+", "".join(tup))
        deviceId = "".join(tupnum)
        return deviceId
