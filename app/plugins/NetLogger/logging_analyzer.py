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

# logging.basicConfig(level=logging.DEBUG,
#                     format='[%(levelname)s] (%(threadName)-10s) %(message)s',
#                     )

ANDROID_SHELL = "/system/bin/sh"

__all__ = ['LoggingAnalyzer', 'MultiPartForm']


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
            # TODO: print to screen
            # print "debug 58, file uploaded has been renamed to %s" % uploaded_file
            # shutil.copyfile(filename, uploaded_file)
            util.run_shell_cmd("cp %s %s" % (filename, uploaded_file))
            os.remove(filename)
        finally:
            util.detach_thread()


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
        fupload = open(filename, 'rb')
        body = fupload.read()
        fupload.close()
        if mimetype is None:
            mimetype = mimetypes.guess_type(
                filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        parts = []
        part_boundary = '--' + self.boundary
        parts.extend([part_boundary,
                      'Content-Disposition: form-data; name="%s"; filename="%s"' % (name,
                                                                                    value)] for name,
                     value in self.form_fields)

        parts.extend(
            [
                part_boundary,
                'Content-Disposition: file; name="%s"; filename="%s"' %
                (field_name,
                 filename),
                'Content-Type: %s' %
                content_type,
                '',
                body,
            ] for field_name,
            filename,
            content_type,
            body in self.files)

        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)


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
                self.__dec_log_name = "diag_log_" + \
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
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

        if not os.path.exists(self.__log_dir):
            os.makedirs(self.__log_dir)
        if not os.path.exists(self.__dec_log_dir):
            os.makedirs(self.__dec_log_dir)

        self.add_source_callback(self._logger_filter)

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
            self.__log_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
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
            self.__dec_log_name = "mi2log_" + \
                datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
            self.__dec_log_path = os.path.join(
                self.__dec_log_dir, self.__dec_log_name)
            # TODO: use log formatter, print to screen
            self.log_info(
                "MobileInsight (NetLogger): decoded cellular log being saved to %s, please check." %
                self.__dec_log_path)
            self.__raw_msg.clear()  # reset the dict
            self.__msg_cnt = 0

    def _save_log(self):
        orig_base_name = os.path.basename(self.__orig_file)
        orig_dir_name = os.path.dirname(self.__orig_file)
        milog_base_name = "diag_log_%s_%s_%s.mi2log" % (
            self.__log_timestamp, util.get_phone_info(), util.get_operator_info())
        milog_abs_name = os.path.join(self.__log_dir, milog_base_name)
        # util.run_shell_cmd("cp %s %s" % (self.__orig_file, milog_abs_name))
        # try:
        #     util.run_shell_cmd("rm %s" % self.__orig_file)
        # except:
        #     pass

        # Yuanjie: eliminate root operations
        shutil.copyfile(self.__orig_file, milog_abs_name)
        os.remove(self.__orig_file)

        return milog_abs_name
