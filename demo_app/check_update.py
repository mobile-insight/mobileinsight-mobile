import kivy
kivy.require('1.0.9')

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.properties import *
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock

from jnius import autoclass, cast

import urllib
import json
import re
import os
import threading
import re
import datetime

import main_utils

__all__=["check_update"]

Builder.load_string('''
<ConfirmPopup>:
    cols:1
    Label:
        text: root.text
        size_hint_y: 16
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


def install_apk(apk_path):
    IntentClass = autoclass("android.content.Intent")
    FileClass = autoclass("java.io.File")
    Uri = autoclass('android.net.Uri')
    f = FileClass(apk_path)
    if not f.exists():
        return
    intent = IntentClass()
    intent.setAction(IntentClass.ACTION_VIEW)
    # intent.setDataAndType(Uri.fromFile(f), "application/vnd.android.package-archive")
    intent.setDataAndType(Uri.parse("file://" + f.toString()), "application/vnd.android.package-archive")
    cur_activity.startActivity(intent)

def download_thread(apk_url, apk_path):
    try:
        urllib.urlretrieve(apk_url, apk_path)
        install_apk(apk_path)
    finally:
        main_utils.detach_thread()

def download_apk(instance, answer):
    global popup
    if answer=="yes":
        global apk_url
        apk_path = os.path.join(main_utils.get_mobile_insight_path(),"update.apk")
        if os.path.isfile(apk_path):
            os.remove(apk_path)

        t = threading.Thread(target=download_thread, args=(apk_url, apk_path))
        t.start()

        progress_bar = ProgressBar()
        progress_bar.value = 1
        def download_progress(instance):
            def next_update(dt):
                if progress_bar.value>=100:
                    return False
                progress_bar.value += 1
            Clock.schedule_interval(next_update, 1/25)

        progress_popup = Popup(
            title='Downloading MobileInsight...',
            content=progress_bar
        )

        progress_popup.bind(on_open=download_progress)
        progress_popup.open()

    popup.dismiss()

def check_update():
    """
    Check if latest version exists
    """
    global apk_url

    update_meta_url = "http://metro.cs.ucla.edu/mobile_insight/update_meta.json"
    update_meta_path = os.path.join(get_cache_dir(), "update_meta.json")

    if os.path.isfile(update_meta_path):
        os.remove(update_meta_path)

    # retrieve latest metadata
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

        content = ConfirmPopup(text='New updates in v'+update_meta["Version"]
                                   +':\n '+update_meta["Description"]
                                   +'Would you like to update?')
        content.bind(on_answer=download_apk)
        popup = Popup(title='New update is available',
                            content=content,
                            size_hint=(None, None),
                            size=(1000,800),
                            auto_dismiss= False)
        popup.open()
