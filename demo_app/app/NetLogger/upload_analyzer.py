'''
upload_analyzer.py

This code analyses newly generated QMDL log file,
renames it and uploads to the server.

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

from mobile_insight.analyzer import Analyzer
from mi2app_utils import get_cache_dir
from jnius import autoclass  # SDcard Android

ANDROID_SHELL = "/system/bin/sh"

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return
    
    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
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
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the request.
        # Each part is separated by a boundary string.
        # Once the list is built, return a string where each line is separated by '\r\n'.  
        parts = []
        part_boundary = '--' + self.boundary
        
        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )
        
        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )
        
        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)

class UploadAnalyzer(Analyzer):
    """
    A upload ananlyzer for QMDL log processing and uploading
    """

    def __init__(self):
        Analyzer.__init__(self)

        self.__upload = False           # upload decision
        self.__original_filename = ""   # upload filename

        # init packet filters
        self.add_source_callback(self.__upload_filter)

    def __upload_filter(self, msg):
        """
        Callback to process upload requests.

        :param msg: the upload message (qmdl file location) from trace collector.
        :type msg: Event
        """
        if msg.type_id.find("new_diag_log") != -1: # found new qmdl file
            print "msg type found"
            self.__log_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            print "the timestamp is "+self.__log_timestamp
            self.__upload = True
            self.__original_filename = msg.data
            uploadcmd = "su -c chmod 644 " + self.__original_filename
            proc = subprocess.Popen(uploadcmd, executable = ANDROID_SHELL, shell = True)
            proc.wait()
            uploadfilename = self.__callback_rename_file()
            self.__upload_qmdl_log(uploadfilename)

    def __get_device_id(self):
        """
        Get unique device ID for renaming propose. It may not work under Android 5.0 (unverified)
        # root@kltetmo:/ # dumpsys iphonesubinfo
        # Phone Subscriber Info:
        #   Phone Type = GSM
        #   Device ID = 351881062060429
        Incase "su -c dumpsys iphonesubinfo" not working, we should use commands:
        # root@kltetmo:/ # service call iphonesubinfo 1
        # Result: Parcel(
        #   0x00000000: 00000000 0000000f 00350033 00380031 '........3.5.1.8.'
        #   0x00000010: 00310038 00360030 00300032 00300036 '8.1.0.6.2.0.6.0.'
        #   0x00000020: 00320034 00000039                   '4.2.9...        ')
        cmd = "service call iphonesubinfo 1 | busybox awk -F \"'\" '{print $2}' | busybox sed 's/[^0-9A-F]*//g' | busybox tr -d '\n' && echo"
        out = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        print "upload_analyzer.py: __get_device_id = "+out
        return out.communicate()[0]
        # another solution: Sending AT+CGSN through the appropriate serial device will have it return the IMEI.
        """
        # original func call -- does not work on Android 5.0+ device
        # cmd = "su -c dumpsys iphonesubinfo"
        # ANDROID_SHELL = "/system/bin/sh"
        # proc = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
        # for line in proc.stdout:
        #     if "Device ID" in line:
        #         deviceId = re.findall("\d+", line)[0] # find the number in the line
        #         proc.kill()
        #         break
        # proc.wait()
        # return deviceId

        cmd = "su -c service call iphonesubinfo 1"
        proc = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
        out = proc.communicate()[0]
        tup = re.findall("\'.+\'", out)
        tupnum = re.findall("\d+", "".join(tup))
        deviceId = "".join(tupnum)
        return deviceId

    def __get_phone_info(self):
        """
        Get unique phone info for renaming propose.
        format: <deviceID>_<manufacturer>-<model>_<operator>
        # root@kltetmo:/ # getprop
        # [gsm.operator.alpha]: [AT&T]
        # [gsm.version.baseband]: [G900TUVU1BNG3]
        # [ro.product.brand]: [samsung]
        # [ro.product.manufacturer]: [samsung]
        # [ro.product.model]: [SM-G900T]
        """
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
        """
        Rename log file's name to fit in server's parser
        format: diag_log_<timestamp>_<deviceID>_<manufacturer>-<model>_<operator>.mi2log
        """

        cmd = "su -c getprop"
        uploaddir = "/sdcard/mobile_insight_log"
        # print "uploaddir = " + uploaddir

        if not os.path.exists(uploaddir):
            os.makedirs(uploaddir)

        qmdlfilebasename = os.path.basename(self.__original_filename)
        qmdlfiledirname = os.path.dirname(self.__original_filename)
        # uploadfilebasename = qmdlfilebasename.split('.')[0] + '_' + self.__get_phone_info() + '.mi2log'
        uploadfilebasename = "diag_log_" + self.__log_timestamp + '_' + self.__get_phone_info() + '.mi2log'
        uploadfileabsname = os.path.join(uploaddir + '/' + uploadfilebasename)

        print "original filename = " + self.__original_filename
        print "uploadfileabsname = " + uploadfileabsname

        shutil.copyfile(self.__original_filename, uploadfileabsname)

        # this old command no longer work on the Nexus 6P
        # uploadcmd = "su -c cp " + self.__original_filename + " " + uploadfileabsname
        # proc = subprocess.Popen(uploadcmd, executable = ANDROID_SHELL, shell = True)
        # proc.wait()
        print "file copied to sdcard"

        # deletecmd = "su -c rm " + self.__original_filename
        # proc = subprocess.Popen(deletecmd, executable = ANDROID_SHELL, shell = True)
        # proc.wait()

        os.remove(self.__original_filename)
        print "temporary log deleted"
        
        return uploadfileabsname

    def __upload_qmdl_log(self, filename):
        """
        Upload the new log file to the server
        Server URL: http://metro.cs.ucla.edu/mobile_insight/
        Server PHP: http://metro.cs.ucla.edu/mobile_insight/upload_file.php
        """

        # Add the file for uploading
        form = MultiPartForm()
        form.add_file('file', filename)
        
        # Build the request
        request = urllib2.Request('http://metro.cs.ucla.edu/mobile_insight/upload_file.php')
        request.add_header("Connection", "Keep-Alive")
        request.add_header("ENCTYPE", "multipart/form-data")
        request.add_header('Content-Type', form.get_content_type())
        body = str(form)
        request.add_data(body)

        # print 'upload_analyzer.py: __upload_qmdl_log SERVER RESPONSE:'
        print "trying to upload log to the server"
        try:
            print urllib2.urlopen(request).read()
        except urllib2.URLError, e:
            upload_fail_dir = "/sdcard/mobile_insight_log/failed_upload"
            if not os.path.exists(upload_fail_dir):
                os.makedirs(upload_fail_dir)
            shutil.move(filename, upload_fail_dir)
            print "upload failed, log saved to the /sdcard/mobile_insight_log/failed_upload"