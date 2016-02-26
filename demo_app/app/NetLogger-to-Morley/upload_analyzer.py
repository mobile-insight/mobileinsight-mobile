'''
upload_analyzer.py

Author: Zengwen Yuan
Version: 2.0
'''

import os
import re
import sys
import subprocess
import datetime
import shutil
import itertools
import mimetools
import mimetypes
import urllib
import urllib2
import logging

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

# from mobile_insight.monitor import QmdlReplayer
from mobile_insight.analyzer import Analyzer
from mi2app_utils import get_cache_dir
from jnius import autoclass  # SDcard Android

ANDROID_SHELL = "/system/bin/sh"

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
        parts.extend([ part_boundary,'Content-Disposition: form-data; name="%s"' % name,'',value,]
            for name, value in self.form_fields)

        parts.extend([ part_boundary, 'Content-Disposition: file; name="%s"; filename="%s"' % (field_name, filename),
              'Content-Type: %s' % content_type, '', body,]
            for field_name, filename, content_type, body in self.files)

        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)

class UploadAnalyzer(Analyzer):

    def __init__(self):
        Analyzer.__init__(self)

        self.__original_filename = ""
        self.__decodemsg = []
        self.__msg_cnt = 0
        self.__save_path = "/sdcard/mobile_insight_log/"
        if not os.path.exists(self.__save_path):
            os.makedirs(self.__save_path)
        # self.__save_filename = "mobile_insight_log_20160101_000000.txt"
        # self.__output_abspath = "/sdcard/mobile_insight_log/mobile_insight_log_20160101_000000.txt"
        self.__save_filename = "mobile_insight_log_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
        self.__output_abspath = os.path.join(self.__save_path, self.__save_filename)

        self.add_source_callback(self.__upload_filter)

    def __save_decoded_log(self):
        # self.__save_filename = "mobile_insight_log_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + ".txt"
        # self.__output_abspath = os.path.join(self.__save_path, self.__save_filename)
        # print "__save_decoded_log() path = " + self.__output_abspath
        with open(self.__output_abspath, 'a') as f:
            f.writelines(self.__decodemsg)
        self.__decodemsg = []
        # self.__msg_cnt = 0

    def __upload_filter(self, msg):
        """
        Callback to process upload requests.

        :param msg: the upload message (qmdl file location) from trace collector.
        :type msg: Event
        """
        if (msg.type_id.startswith("LTE_") or msg.type_id.startswith("WCDMA_") or msg.type_id.startswith("UMTS_")):
            log_item = msg.data.decode()
            log_item_dict = dict(log_item)
            if not log_item_dict.has_key('Msg'):
                return
            self.__decodemsg.append("type_id: %s\n" % str(log_item_dict["type_id"]))
            self.__decodemsg.append("timestamp: %s GMT\n" % str(log_item_dict["timestamp"]))
            self.__decodemsg.append(log_item_dict['Msg'])
            self.__msg_cnt += 1
            logging.info("msg count = %d\n" % self.__msg_cnt)
            # if self.__msg_cnt >= 20:
            #     self.__save_decoded_log()
            self.__save_decoded_log()

        if msg.type_id.find("new_diag_log") != -1:
            self.__log_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.__upload = True
            self.__original_filename = msg.data
            uploadcmd = "su -c chmod 644 " + self.__original_filename
            proc = subprocess.Popen(uploadcmd, executable = ANDROID_SHELL, shell = True)
            proc.wait()
            uploadfilename = self.__callback_rename_file()
            self.__upload_qmdl_log(uploadfilename)

    def __get_device_id(self):
        cmd = "su -c service call iphonesubinfo 1"
        proc = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
        out = proc.communicate()[0]
        tup = re.findall("\'.+\'", out)
        tupnum = re.findall("\d+", "".join(tup))
        deviceId = "".join(tupnum)
        return deviceId

    def __get_phone_info(self):
        cmd = "su -c getprop"
        modelFound = False
        manufacturerFound = False
        operatorFound = False
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
            if modelFound and manufacturerFound and operatorFound:
                proc.kill()
                break
        proc.wait()
        if operator == "":
            operator = "null"
        return self.__get_device_id() + '_' + manufacturer + '-' + model + '_' + operator

    def __callback_rename_file(self):
        uploaddir = "/sdcard/mobile_insight_log/"

        if not os.path.exists(uploaddir):
            os.makedirs(uploaddir)

        logfilebasename = os.path.basename(self.__original_filename)
        logfiledirname = os.path.dirname(self.__original_filename)
        uploadfilebasename = "diag_log_" + self.__log_timestamp + '_' + self.__get_phone_info() + '.mi2log'
        uploadfileabsname = os.path.join(logfiledirname + '/' + uploadfilebasename)

        logging.info("original filename = " + self.__original_filename)
        logging.info("uploadfileabsname = " + uploadfileabsname)

        shutil.copyfile(self.__original_filename, uploadfileabsname)
        os.remove(self.__original_filename)

        return uploadfileabsname

    def __upload_qmdl_log(self, filename):
        form = MultiPartForm()
        form.add_file('file', filename)
        request = urllib2.Request('http://metro.cs.ucla.edu/mobile_insight/upload_file.php')
        request.add_header("Connection", "Keep-Alive")
        request.add_header("ENCTYPE", "multipart/form-data")
        request.add_header('Content-Type', form.get_content_type())
        body = str(form)
        request.add_data(body)
        try:
            logging.info("MobileInsight2 (NetLogger): server's response -- " + urllib2.urlopen(request).read())
        except urllib2.URLError, e:
            logging.info("MobileInsight2 (NetLogger): upload failed, just smile :)")
        os.remove(filename)
