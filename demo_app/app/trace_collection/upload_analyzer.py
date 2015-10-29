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
import itertools
import mimetools
import mimetypes
import urllib
import urllib2

from mobile_insight.analyzer import Analyzer

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
        if msg.type_id.find("new_qmdl_file") != -1: # found new qmdl file
            self.__upload = True
            self.__original_filename = msg.data
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
        ANDROID_SHELL = "/system/bin/sh"
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
        ANDROID_SHELL = "/system/bin/sh"
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
        return self.__get_device_id() + '_' + manufacturer + '-' + model + '_' + operator

    def __callback_rename_file(self):
        """
        Rename log file's name to fit in server's parser
        format: diag_log_<timestamp>_<deviceID>_<manufacturer>-<model>_<operator>.qmdl
        original absolute file name:
        /data/data/org.wing.mobile_insight2/cache/mobile_insight_log/diag_log_20151023_190031.qmdl
        renameed file name:
        /data/data/org.wing.mobile_insight2/cache/upload_log/diag_log_20151023_190031_351881062060429_Samsung-SM-G900T_AT&T.qmdl
        """
        # self.__original_filename = '/data/data/org.wing.mobile_insight2/cache/mobile_insight_log/diag_log_20151023_190031.qmdl'
        # qmdlfilebasename = 'diag_log_20151023_190031.qmdl'
        # qmdlfiledirname = '/data/data/org.wing.mobile_insight2/cache/mobile_insight_log'
        # uploaddir = '/data/data/org.wing.mobile_insight2/cache/log_upload'
        # uploadfilebasename = 'diag_log_20151023_190031_351881062060429_Samsung-SM-G900T_AT&T.qmdl'
        # uploadfileabsname = '/data/data/org.wing.mobile_insight2/cache/log_upload/diag_log_20151023_190031_351881062060429_Samsung-SM-G900T_AT&T.qmdl'
        qmdlfilebasename = os.path.basename(self.__original_filename)
        qmdlfiledirname = os.path.dirname(self.__original_filename)
        uploaddir = os.path.join(os.path.dirname(qmdlfiledirname) + '/log_upload')
        uploadfilebasename = qmdlfilebasename.split('.')[0] + '_' + self.__get_phone_info() + '.qmdl'
        uploadfileabsname = os.path.join(uploaddir + '/' + uploadfilebasename)
        
        if not os.path.exists(uploaddir):
            os.makedirs(uploaddir)

        os.rename(self.__original_filename, uploadfileabsname) # move file to new folder and rename
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

        print 'upload_analyzer.py: __upload_qmdl_log SERVER RESPONSE:'
        print urllib2.urlopen(request).read()