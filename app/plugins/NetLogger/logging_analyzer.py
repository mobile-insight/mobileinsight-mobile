'''
logging_analyzer.py

It analyses newly generated cellular event log file,
log and decode them, then save the log to external storage.

Author  : Zengwen Yuan
Version : 3.1  Attempt upload again when WiFi is available
          3.0  Add uploading function
          2.0  Save decoded log to sdcard
          1.0  Init NetLogger
'''

from android.broadcast import BroadcastReceiver
from jnius import autoclass
from mobile_insight.analyzer import Analyzer
from service import mi2app_utils as util

import datetime
import itertools
import logging
import mimetools
import mimetypes
import os
import shutil
import subprocess
import threading
import time
import urllib
import urllib2

# logging.basicConfig(level=logging.DEBUG,
#                     format='[%(levelname)s] (%(threadName)-10s) %(message)s',
#                     )

ANDROID_SHELL = "/system/bin/sh"

__all__ = ['LoggingAnalyzer']


def upload_log(filename):
    succeed = False
    form = MultiPartForm()
    form.add_field('file[]', filename)
    form.add_file('file', filename)
    request = urllib2.Request(
        'http://metro.cs.ucla.edu/mobile_insight/upload_file.php')
    request.add_header("Connection", "Keep-Alive")
    request.add_header("ENCTYPE", "multipart/form-data")
    request.add_header('Content-Type', form.get_content_type())
    body = str(form)
    request.add_data(body)

    try:
        response = urllib2.urlopen(request, timeout=3).read()
        if response.startswith("TW9iaWxlSW5zaWdodA==FILE_SUCC") \
                or response.startswith("TW9iaWxlSW5zaWdodA==FILE_EXST"):
            succeed = True
    except urllib2.URLError as e:
        pass
    except socket.timeout as e:
        pass

    if succeed is True:
        try:
            file_base_name = os.path.basename(filename)
            uploaded_file = os.path.join(
                util.get_mobileinsight_log_uploaded_path(), file_base_name)
            # shutil.copyfile(filename, uploaded_file)
            util.run_shell_cmd("cp %s %s" % (filename, uploaded_file))
            os.remove(filename)
            self.log_info("File %s has been uploaded successfully" % uploaded_file)
        finally:
            util.detach_thread()


class LoggingAnalyzer(Analyzer):
    """
    An analyzer for cellular events logging and decoding
    """

    def __init__(self, config):
        Analyzer.__init__(self)

        self.__log_dir = util.get_mobileinsight_log_path()
        self.__dec_log_dir = util.get_mobileinsight_log_decoded_path()
        self.__orig_file = ""
        self.__raw_msg = {}
        self.__raw_msg_key = ""
        self.__msg_cnt = 0
        self.__dec_msg = []
        self.__is_wifi_enabled = False
        self.__log_timestamp = ""
        self.__use_tcpdump = False
        self.__iface = "wlan0"
        self.__ping_on = False
        self.__ping_int = 1
        self.__ping_addr = "www.google.com"

        self._read_config(config)

        if not os.path.exists(self.__log_dir):
            os.makedirs(self.__log_dir)
        if not os.path.exists(self.__dec_log_dir):
            os.makedirs(self.__dec_log_dir)

        self.add_source_callback(self._logger_filter)

        self.br = BroadcastReceiver(self.on_broadcast,
                actions=['MobileInsight.Main.StopService'])
        self.br.start()

        self._kill_grep_thread("tcpdump")
        self._kill_grep_thread("ping")
        self._run_tcpdump()
        self._run_ping()


    def _run_tcpdump(self):
        if self.__use_tcpdump is True:
            self.__pcap_file = os.path.join(
                self.__log_dir,
                ("mi_" + self.get_cur_timestamp() + ".pcap"))
            self.log_info("Generating pcap log file: %s" % self.__pcap_file)
            util.run_root_shell_cmd(
                "tcpdump -i %s -w %s &" % (self.__iface, self.__pcap_file))


    def _run_ping(self):
        if self.__ping_on is True:
            self.log_warning(
                "Generating periodic traffic by pinging %s" %
                self.__ping_addr)
            util.run_shell_cmd(
                "ping -c 20 -i %d %s &" %
                (self.__ping_int, self.__ping_addr))
            self.log_warning("I pinged 20 packets!")


    def _read_config(self, config):
        try:
            if config['is_use_wifi'] == '1':
                self.__is_use_wifi = True
            else:
                self.__is_use_wifi = False
        except BaseException:
            self.__is_use_wifi = False
        try:
            if config['is_dec_log'] == '1':
                self.__is_dec_log = True
                self.__dec_log_name = "diag_log_" + self.get_cur_timestamp() + ".txt"
                self.__dec_log_path = os.path.join(
                    self.__dec_log_dir, self.__dec_log_name)
            else:
                self.__is_dec_log = False
        except BaseException:
            self.__is_dec_log = False
        try:
            self.__dec_log_type = config['log_type']
        except BaseException:
            self.__dec_log_type = ""

        try:
            if config['use_tcpdump'] == '1':
                self.__use_tcpdump = True
        except BaseException:
            pass
        try:
            self.__iface = config['iface']
        except BaseException:
            pass
        try:
            if config['ping_on'] == '1':
                self.__ping_on = True
        except BaseException:
            pass
        try:
            self.__ping_int = int(config['ping_int']) / 1000
        except BaseException:
            pass
        try:
            self.__ping_addr = config['ping_addr']
        except BaseException:
            pass

    def __del__(self):
        self.log_info("__del__ is called")

    def _kill_grep_thread(self, proc_name):
        # sample ps output
        # root      10108 1     5116   2748  poll_sched 00001226bc S tcpdump
        proc = subprocess.Popen(
            "su -c ps | grep -i %s" %
            proc_name,
            executable=ANDROID_SHELL,
            shell=True,
            stdout=subprocess.PIPE)
        try:
            match_lines = proc.communicate()[0].split('\n')[:-1]
            for match in match_lines:
                self.log_debug("Thread match = %s" % match)
                ps_num = match.split()[1]
                try:
                    self.log_info(
                        "Killing previous %s thread, pid = %s" %
                        (proc_name, ps_num))
                    util.run_shell_cmd("su -c kill -9 %s" % ps_num)
                except BaseException:
                    self.log_warning(
                        "Some exception happens for killing %s" %
                        proc_name)
                    pass
        except BaseException:
            self.log_warning(
                "Some exception happens for getting %s threads" %
                proc_name)
            pass


    # TODO (Zengwen): move to the util function
    def get_cur_timestamp(self):
        return str(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))

    # TODO (Zengwen): move to the util function
    def get_last_mod_timestamp(self, file):
        return str(time.strftime('%Y%m%d_%H%M%S',
                time.localtime(os.path.getmtime(file))))


    def on_broadcast(self, context, intent):
        '''
        This plugin is going to be stopped, finish closure work
        '''
        self.log_info("MobileInsight.Main.StopService is received")
        self._check_orphan_log()

        IntentClass = autoclass("android.content.Intent")
        intent = IntentClass()
        action = 'MobileInsight.Plugin.StopServiceAck'
        intent.setAction(action)
        try:
            util.pyService.sendBroadcast(intent)
        except Exception as e:
            import traceback
            self.log_error(str(traceback.format_exc()))

    def _check_orphan_log(self):
        '''
        Check if there is any orphan log left in cache folder
        '''
        dated_files = []
        mi2log_folder = os.path.join(util.get_cache_dir(), "mi2log")
        orphan_filename = ""
        for subdir, dirs, files in os.walk(mi2log_folder):
            for f in files:
                fn = os.path.join(subdir, f)
                dated_files.append((os.path.getmtime(fn), fn))
        dated_files.sort()
        dated_files.reverse()
        for dated_file in dated_files:
            self.__orig_file = dated_file[1]
            # print "self.__orig_file = %s" % str(self.__orig_file)
            # print "self.__orig_file modified time = %s" % str(time.strftime('%Y%m%d_%H%M%S', time.localtime(os.path.getmtime(self.__orig_file))))
            util.run_shell_cmd("chmod 644 %s" % self.__orig_file)
            orphan_filename = self._save_log()
            self.log_info("Found undersized orphan log, file saved to %s" % orphan_filename)

    def __del__(self):
        self.log_info("__del__ is called")


    def _logger_filter(self, msg):
        """
        Callback to process new generated logs.

        :param msg: the message from trace collector.
        :type msg: Event
        """

        # when a new log comes, save it to external storage and upload
        if msg.type_id.find("new_diag_log") != -1:
            self.__log_timestamp = self.get_cur_timestamp()
            self.__orig_file = msg.data.decode().get("filename")

            # FIXME (Zengwen): the change access command is a walkaround
            # solution
            util.run_shell_cmd("chmod 644 %s" % self.__orig_file)

            self._save_log()
            self.__is_wifi_enabled = util.get_wifi_status()

            if self.__is_use_wifi is True and self.__is_wifi_enabled is True:
                try:
                    for f in os.listdir(self.__log_dir):
                        if f.endswith(".mi2log"):
                            orphan_file = os.path.join(self.__log_dir, f)
                            t = threading.Thread(
                                target=upload_log, args=(orphan_file, ))
                            t.start()
                except Exception as e:
                    pass
            else:
                # use cellular data to upload. Skip for now.
                pass

        if self.__is_dec_log is True:
            if self.__dec_log_type == "LTE Control Plane":
                if (msg.type_id.startswith("LTE_RRC")
                        or msg.type_id.startswith("LTE_NAS")):
                    self._decode_msg(msg)
            elif self.__dec_log_type == "LTE Control/Data Plane":
                if (msg.type_id.startswith("LTE")
                        and not msg.type_id.startswith("LTE_PHY")):
                    self._decode_msg(msg)
            elif self.__dec_log_type == "LTE Control/Data/PHY":
                if (msg.type_id.startswith("LTE")):
                    self._decode_msg(msg)
            elif self.__dec_log_type == "LTE/3G Control Plane":
                if ("RRC" in msg.type_id or "NAS" in msg.type_id):
                    self._decode_msg(msg)
            elif self.__dec_log_type == "All":
                if (msg.type_id.startswith("LTE") or msg.type_id.startswith(
                        "WCDMA") or msg.type_id.startswith("UMTS")):
                    self._decode_msg(msg)
            else:
                pass
        else:
            pass

    def _decode_msg(self, msg):
        self.__raw_msg[self.__msg_cnt] = msg.data
        self.__msg_cnt += 1
        if len(self.__raw_msg) >= 20:
            try:
                with open(self.__dec_log_path, 'a') as f:
                    for key in self.__raw_msg:
                        log_item = self.__raw_msg[key].decode_xml()
                        f.writelines(log_item)
            except BaseException:
                pass
            self.__raw_msg.clear()  # reset the dict
        if self.__msg_cnt >= 200:  # open a new file
            self.__dec_log_name = "mi2log_" + self.get_cur_timestamp() + ".txt"
            self.__dec_log_path = os.path.join(
                self.__dec_log_dir, self.__dec_log_name)
            self.log_info(
                "NetLogger: decoded cellular log being saved to %s, please check." %
                self.__dec_log_path)
            self.__raw_msg.clear()  # reset the dict
            self.__msg_cnt = 0


    def _save_log(self):
        self.__log_timestamp = self.get_last_mod_timestamp(self.__orig_file)
        milog_base_name = "diag_log_%s_%s_%s.mi2log" % (
            self.__log_timestamp, util.get_phone_info(), util.get_operator_info())
        milog_abs_name = os.path.join(self.__log_dir, milog_base_name)
        shutil.copyfile(self.__orig_file, milog_abs_name)
        os.remove(self.__orig_file)

        self._kill_grep_thread("tcpdump")
        self._kill_grep_thread("ping")
        self._run_tcpdump()
        self._run_ping()

        return milog_abs_name
