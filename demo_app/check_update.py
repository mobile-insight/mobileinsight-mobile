import kivy
kivy.require('1.0.9')

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.properties import *

from jnius import autoclass, cast

import urllib
import json
import re
import os

import subprocess
from os.path import basename
import re
import datetime
ANDROID_SHELL = "/system/bin/sh"

__all__=["check_update"]

Builder.load_string('''
<ConfirmPopup>:
    cols:1
    Label:
        text: root.text
        size_hint_y: None
    Label:
        text: 'Would like to update?'
        size_hint_y: None
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


cur_activity = cast("android.app.Activity", autoclass("org.renpy.android.PythonActivity").mActivity)
apk_url = ""
popup = None


class ConfirmPopup(GridLayout):
    text = StringProperty()
    
    def __init__(self,**kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup,self).__init__(**kwargs)
        
    def on_answer(self, *args):
        pass   

def get_cache_dir():
    return str(cur_activity.getCacheDir().getAbsolutePath())

def get_cur_version():
    """
    Get current apk version string
    """
    pkg_name = cur_activity.getPackageName()
    return str(cur_activity.getPackageManager().getPackageInfo(pkg_name, 0).versionName)

def cmp_version(version1, version2):
    '''
    Compare two version numbers

    :param version1: version number 1
    :type version1: string
    :param version2: version number 2
    :type version2: string
    :returns: 0 if version1==version2, 1 if version1>version2, -1 if version1<version2
    '''
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
    return cmp(normalize(version1), normalize(version2))


def download_apk(instance, answer):
    global popup
    if answer=="yes":
        global apk_url
        apk_path = os.path.join(get_cache_dir(), "update.apk") 
        urllib.urlretrieve (apk_url, apk_path)

    popup.dismiss()

def check_update():
    """
    Check if latest version exists
    """
    global apk_url

    update_meta_url = "http://metro.cs.ucla.edu/mobile_insight/update_meta.json"
    update_meta_path = os.path.join(get_cache_dir(), "update_meta.json")
    urllib.urlretrieve (update_meta_url, update_meta_path)

    if not os.path.isfile(update_meta_path):
        return

    raw_data = open(update_meta_path).read()
    update_meta = json.loads(raw_data)

    if "Version" not in update_meta:
        return
         

    cur_version = get_cur_version()
    apk_url = update_meta["URL"]

    if cmp_version(cur_version,update_meta['Version'])<0:


    	global popup

        content = ConfirmPopup(text='New updates:\n '+update_meta["Description"])
        content.bind(on_answer=download_apk)
        popup = Popup(title='New version '+update_meta["Version"]+' is available',
                            content=content,
                            size_hint=(None, None),
                            size=(1200,600),
                            auto_dismiss= False)
        popup.open()
            
