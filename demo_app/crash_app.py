import kivy
kivy.require('1.0.9')

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.properties import *

import subprocess
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
        
    def _on_answer(self, instance, answer):
        phone_info = get_phone_info()
        log_name= "/sdcard/crash_report_" \
                + phone_info+'_' \
                + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') \
                + '.txt'
        run_shell_cmd('logcat -d | grep -E "python|diag" >'+log_name,True)
        self.popup.dismiss()
