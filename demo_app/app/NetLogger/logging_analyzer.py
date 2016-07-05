'''
logging_analyzer.py

It analyses newly generated cellular event log file,
log and decode them, then save the log to external storage.

Author: Zengwen Yuan
Version: 3.1  Attempt upload again when WiFi is available
         3.0  Add uploading function
         2.0  Save decoded log to sdcard
         1.0  Init NetLogger
'''

import os
import time
import shutil
import urllib
import urllib2
import logging
import datetime
import itertools
import mimetools
import mimetypes
import threading
import subprocess

from mobile_insight.analyzer import Analyzer
import mi2app_utils as util

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

ANDROID_SHELL = "/system/bin/sh"

__all__ = ['LoggingAnalyzer', 'MultiPartForm']

def upload_log(filename):
    logging.debug('Starting')
    print "debug 38, ", threading.currentThread().getName(), 'Starting'

    succeed = False
    form = MultiPartForm()
    form.add_field('file[]', filename)
    form.add_file('file', filename)
    request = urllib2.Request('http://metro.cs.ucla.edu/mobile_insight/upload_file.php')
    request.add_header("Connection", "Keep-Alive")
    request.add_header("ENCTYPE", "multipart/form-data")
    request.add_header('Content-Type', form.get_content_type())
    body = str(form)
    request.add_data(body)

    try:
        response = urllib2.urlopen(request, timeout = 3).read()
        # print "debug 52: server's response -- " + response
        if response.startswith("TW9iaWxlSW5zaWdodA==FILE_SUCC") \
        or response.startswith("TW9iaWxlSW5zaWdodA==FILE_EXST"):
            succeed = True
    except urllib2.URLError, e:
        # print "debug 63: upload failed (url error), file has been staged and will be uploaded again"
        pass
    except socket.timeout as e:
        # print "debug 70: upload failed (timeout), file has been staged and will be uploaded again"
        pass

    if succeed is True:
        try:
            file_base_name = os.path.basename(filename)
            uploaded_file  = os.path.join(util.get_mobile_insight_log_uploaded_path(), file_base_name)
            # TODO: print to screen
            # print "debug 58, file uploaded has been renamed to %s" % uploaded_file
            shutil.copyfile(filename, uploaded_file)
            os.remove(filename)
        finally:
            # very import since we are using thread.
            # otherwise JVM will complain that
            # Native thread exiting without having called DetachCurrentThread
            util.detach_thread()

    logging.debug('Exiting')
    # print "debug 75", threading.currentThread().getName(), 'detach and Exiting'


class MultiPartForm(object):

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, mimetype=None):
        """Add a file to be uploaded."""
        fupload = open(filename, 'rb')
        body = fupload.read()
        fupload.close()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        parts = []
        part_boundary = '--' + self.boundary
        parts.extend([ part_boundary, 'Content-Disposition: form-data; name="%s"; filename="%s"' % (name, value)]
            for name, value in self.form_fields)

        parts.extend([ part_boundary, 'Content-Disposition: file; name="%s"; filename="%s"' % (field_name, filename),
              'Content-Type: %s' % content_type, '', body,]
            for field_name, filename, content_type, body in self.files)

        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)


class LoggingAnalyzer(Analyzer):
    """
    An ananlyzer for cellular events logging and decoding
    """

    def __init__(self, config):
        Analyzer.__init__(self)

        self.__log_dir           = util.get_mobile_insight_log_path()
        self.__dec_log_dir       = util.get_mobile_insight_log_decoded_path()
        self.__orig_file         = ""
        self.__raw_msg           = {}
        self.__raw_msg_key       = ""
        self.__msg_cnt           = 0
        self.__dec_msg           = []
        self.__is_wifi_enabled   = False

        try:
            if config['is_use_wifi'] == '1':
                self.__is_use_wifi   = True
            else:
                self.__is_use_wifi   = False
        except:
            self.__is_use_wifi       = False
        try:
            if config['is_dec_log']  == '1':
                self.__is_dec_log    = True
                self.__dec_log_name  = "diag_log_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
                self.__dec_log_path  = os.path.join(self.__dec_log_dir, self.__dec_log_name)
            else:
                self.__is_dec_log    = False
        except:
            self.__is_dec_log        = False
        try:
            self.__dec_log_type      = config['log_type']
        except:
            self.__dec_log_type      = ""

        if not os.path.exists(self.__log_dir):
            os.makedirs(self.__log_dir)
        if not os.path.exists(self.__dec_log_dir):
            os.makedirs(self.__dec_log_dir)

        # with open(self.__dec_log_path, 'a') as f:
        #     pass
        # print "MobileInsight (NetLogger): decoded cellular log being saved to %s, please check." % self.__dec_log_path
        # print "debug 140: is_use_wifi = %s, log_type = %s, is_dec_log = %s" % (config['is_use_wifi'], config["log_type"], config["is_dec_log"])
        # print "debug 141: is_use_wifi = %s, log_type = %s, is_dec_log = %s" % (self.__is_use_wifi, self.__dec_log_type, self.__is_dec_log)

        self.add_source_callback(self._logger_filter)

    def _logger_filter(self, msg):
        """
        Callback to process new generated logs.

        :param msg: the message from trace collector.
        :type msg: Event
        """

        # p = subprocess.Popen("su", executable = ANDROID_SHELL, shell = True, \
        #                                 stdin = subprocess.PIPE, stdout = subprocess.PIPE)

        # when a new log comes, save it to external storage and upload
        if msg.type_id.find("new_diag_log") != -1:
            # print "debug 169: a new file coming in"
            self.__log_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.__orig_file     = msg.data.decode().get("filename")

            # FIXME (Zengwen): the change access command is a walkaround solution
            # chmodcmd = "chmod 0644 " + self.__orig_file
            # p.communicate(chmodcmd + '\n')
            # p.wait()
            util.run_shell_cmd("chmod 644 %s" % self.__orig_file)
            # util.detach_thread()

            self._save_log()
            # print "debug 180: file saved"

            self.__is_wifi_enabled = util.get_wifi_status()
            # print "debug 162, self.__is_use_wifi = %s" % self.__is_use_wifi
            # print "debug 163, self.__is_wifi_enabled = %s" % self.__is_wifi_enabled

            if self.__is_use_wifi is True and self.__is_wifi_enabled is True:
                # print "debug 167, now try to upload the new log and orphan logs"
                try:
                    # print "debug 169, I started a new thread for wifi upload"

                    # search for remaining files and try to upload
                    for f in os.listdir(self.__log_dir):
                        if f.endswith(".mi2log"):
                            # print "debug 177, found file = %s, let's upload" % f
                            orphan_file = os.path.join(self.__log_dir, f)
                            t = threading.Thread(target = upload_log, args = (orphan_file, ))
                            # t.setDaemon(True)
                            t.start()
                            # t.join(1)
                except Exception as e:
                    # print e
                    pass
            else:
                # use cellular data to upload. Skip for now.
                pass

        if self.__is_dec_log is True:
            # print "debug 192, I am going to decode this msg!"
            if self.__dec_log_type == "LTE Control Plane":
                if (msg.type_id.startswith("LTE_RRC") or msg.type_id.startswith("LTE_NAS")):
                    self._decode_msg(msg)
            elif self.__dec_log_type == "LTE Control/Data Plane":
                if (msg.type_id.startswith("LTE") and not msg.type_id.startswith("LTE_PHY")):
                    self._decode_msg(msg)
            elif self.__dec_log_type == "LTE Control/Data/PHY":
                if (msg.type_id.startswith("LTE")):
                    self._decode_msg(msg)
            elif self.__dec_log_type == "LTE/3G Control Plane":
                if ("RRC" in msg.type_id or "NAS" in msg.type_id):
                    self._decode_msg(msg)
            elif self.__dec_log_type == "All":
                if (msg.type_id.startswith("LTE") or msg.type_id.startswith("WCDMA") or msg.type_id.startswith("UMTS")):
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
            except:
                pass
            self.__raw_msg.clear()  # reset the dict
        if self.__msg_cnt >= 200:  # open a new file
            self.__dec_log_name = "mi2log_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
            self.__dec_log_path = os.path.join(self.__dec_log_dir, self.__dec_log_name)
            # TODO: use log formatter
            # TODO: print to screen
            self.log_info("MobileInsight (NetLogger): decoded cellular log being saved to %s, please check." % self.__dec_log_path) 
            self.__raw_msg.clear()  # reset the dict
            self.__msg_cnt = 0

    def _save_log(self):
        orig_base_name  = os.path.basename(self.__orig_file)
        orig_dir_name   = os.path.dirname(self.__orig_file)
        milog_base_name = "diag_log_%s_%s_%s.mi2log" % (self.__log_timestamp, util.get_phone_info(), util.get_operator_info())
        milog_abs_name  = os.path.join(self.__log_dir, milog_base_name)
        # Zengwen: try using native copy cmd
        # shutil.copyfile(self.__orig_file, milog_abs_name)

        util.run_shell_cmd("cp %s %s" % (self.__orig_file, milog_abs_name))
        # util.detach_thread()
        # cmd  = "cp %s %s" % (self.__orig_file, milog_abs_name)
        # proc = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
        # out  = proc.communicate()[0]
        # proc.wait()
        try:
            # os.remove(self.__orig_file)
            util.run_shell_cmd("rm %s" % self.__orig_file)
            # util.detach_thread()
            # if out == "":   # saved file, delete original file
            #     print "debug 281, should remove file"
            #     cmd  = "rm %s" % self.__orig_file
            #     proc = subprocess.Popen("su", executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
            #     out  = proc.communicate(cmd + '\n')[0]
            #     print "debug, out = %s" % out
            #     proc.wait()
        except:
            pass
            # print "debug 260: try to remove the original internal log failed"
        return milog_abs_name
