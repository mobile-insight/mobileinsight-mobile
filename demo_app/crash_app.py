import kivy
kivy.require('1.0.9')

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.properties import *

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate, formataddr

import httplib, urllib, urllib2

import subprocess
from os.path import basename
import re
import datetime
ANDROID_SHELL = "/system/bin/sh"

__all__=["ConfirmPopup","CrashApp"]

Builder.load_string('''
<ConfirmPopup>:
    cols:1
    Label:
        text: root.text
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '44sp'
        Button:
            text: 'Yes'
            on_release: root.dispatch('on_answer','yes')
        Button:
            text: 'No'
            on_release: root.dispatch('on_answer', 'no')
''')


def run_shell_cmd(cmd, wait = False):
    p = subprocess.Popen("su", executable=ANDROID_SHELL, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.communicate(cmd+'\n')

    if wait:
        p.wait()
        return p.returncode
    else:
        return None

def get_phone_info():
    cmd          = "getprop ro.product.model; getprop ro.product.manufacturer;"
    proc         = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
    res          = proc.stdout.read().split('\n')
    model        = res[0].replace(" ", "")
    manufacturer = res[1].replace(" ", "")
    phone_info   = get_device_id() + '_' + manufacturer + '-' + model
    return phone_info


def get_opeartor_info():
    cmd          = "getprop gsm.operator.alpha"
    proc         = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
    operator     = proc.stdout.read().split('\n')[0].replace(" ", "")
    if operator == '' or operator is None:
        operator = 'null'
    return operator


def get_device_id():
    cmd = "service call iphonesubinfo 1"
    proc = subprocess.Popen(cmd, executable = ANDROID_SHELL, shell = True, stdout = subprocess.PIPE)
    out = proc.communicate()[0]
    tup = re.findall("\'.+\'", out)
    tupnum = re.findall("\d+", "".join(tup))
    deviceId = "".join(tupnum)
    return deviceId

class ConfirmPopup(GridLayout):
    text = StringProperty()
    
    def __init__(self,**kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup,self).__init__(**kwargs)
        
    def on_answer(self, *args):
        pass    
    

class CrashApp(App):
    def build(self):
        content = ConfirmPopup(text='Would you like to report this bug to us?')
        content.bind(on_answer=self._on_answer)
        self.popup = Popup(title="Opps! MobileInsight exits unexpectedly...",
                            content=content,
                            size_hint=(None, None),
                            size=(1200,600),
                            auto_dismiss= False)
        self.popup.open()

    def __upload_crash_log(self, file_path):

        http_url='http://metro.cs.ucla.edu/mobile_insight/upload_crash_log.php'
        
        # Find log path
        tmp_index = file_path.rfind('/')
        file_name = file_path[tmp_index+1:]

        # Tokens for http POST
        boundary = "----WebKitFormBoundaryEOdH94ZkJz9PCjBh"
        twoHyphens = "--"
        lineEnd = "\r\n"

        # Read the crash log (as http body)
        data = []

        fr=open(file_path,'r')
        data.append(twoHyphens+boundary)
        data.append('Content-Disposition: form-data; name="file[]";filename="'+file_name+ '"')
        data.append('Content-Type: application/octet-stream' + lineEnd)
        data.append(fr.read())
        # data.append(lineEnd)
        fr.close()

        data.append(twoHyphens+boundary)
        data.append('Content-Disposition: form-data;name="submit"'+lineEnd)
        data.append('0x11dd')

        data.append(twoHyphens+boundary+twoHyphens+lineEnd)

        http_body='\r\n'.join(data)

        try:
            #buld http request
            req=urllib2.Request(http_url)
            #header
            req.add_header('Host', 'metro.cs.ucla.edu')
            req.add_header('Cache-Control', 'max-age=0')
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            req.add_header('Accept-Encoding', 'gzip, deflate')
            req.add_header('Connection', 'keep-alive')
            req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
            # req.add_header('file[]',file_name)
            req.add_data(http_body)

            #post data to server
            resp = urllib2.urlopen(req, timeout=5)
            #get response
            qrcont=resp.read()
            
        except Exception,e:
            "Fail to send bug report!"
            import traceback
            print str(traceback.format_exc())
        
    def _on_answer(self, instance, answer):
        if answer=="yes":
            phone_info = get_phone_info()
            log_name= "/sdcard/crash_report_" \
                    + phone_info+'_' \
                    + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') \
                    + '.txt'
            run_shell_cmd('logcat -d | grep -E "python|diag" >'+log_name,True)
            self.__upload_crash_log(log_name)

            

        self.popup.dismiss()
