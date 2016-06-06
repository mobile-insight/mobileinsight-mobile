import kivy
kivy.require('1.0.9')

from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import *

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import platform

from jnius import autoclass, cast

import functools
import os
import shlex
import sys
import subprocess
import time
import traceback

import json

ANDROID_SHELL = "/system/bin/sh"

Window.softinput_mode = "pan"
Window.clearcolor = (1, 1, 1, 1)

Builder.load_file('main_ui.kv')


def get_app_list():

    '''
    Load plugin lists, including both buil-in and 3rd-party plugins
    '''

    current_activity = cast("android.app.Activity",
                            autoclass("org.renpy.android.PythonActivity").mActivity)

    ret = {} # app_name->(path,with_UI)

    APP_DIR = os.path.join(str(current_activity.getFilesDir().getAbsolutePath()), "app")
    l = os.listdir(APP_DIR)
    for f in l:
        if os.path.exists(os.path.join(APP_DIR, f, "main_ui.mi2app")):
            ret[f] = (os.path.join(APP_DIR, f), True)
        elif os.path.exists(os.path.join(APP_DIR, f, "main.mi2app")):
            # ret.append(f)
            ret[f] = (os.path.join(APP_DIR, f), False)

    # Yuanjie: support alternative path for users to customize their own app
    APP_DIR = "/sdcard/mobile_insight/apps/"

    if os.path.exists(APP_DIR):
        l = os.listdir(APP_DIR)
        for f in l:
            if os.path.exists(os.path.join(APP_DIR, f, "main_ui.mi2app")):
                if f in ret:
                    tmp_name = f + " (plugin)"
                else:
                    tmp_name = f
                ret[tmp_name] = (os.path.join(APP_DIR, f), True)
            elif os.path.exists(os.path.join(APP_DIR, f, "main.mi2app")):
                if f in ret:
                    tmp_name = f + " (plugin)"
                else:
                    tmp_name = f
                ret[tmp_name] = (os.path.join(APP_DIR, f), False)
    else: # create directory for user-customized apps
        os.mkdir(APP_DIR)

    return ret

class MobileInsightScreen(GridLayout):
    error_log = StringProperty("MobileInsight 2.0\nUCLA WiNG Group & OSU MSSN Lab")
    collecting = BooleanProperty(False)
    current_activity = cast("android.app.Activity",
                            autoclass("org.renpy.android.PythonActivity").mActivity)
    service = None
    analyzer = None

    def __init__(self):
        super(MobileInsightScreen, self).__init__()
        # self.app_list = self._get_app_list()
        # self.app_list = self.get_app_list()
        self.app_list = get_app_list()
        # self.app_list.sort()

        self.__init_libs()
        self._create_folder()

        if not self.__check_diag_mode():
            self.error_log = "WARINING: the diagnostic mode is disabled. Please check your phone settings."

        # clean up ongoing log collections
        self.stop_collection()  

        first = True
        for name in self.app_list:
            widget = LabeledCheckBox(text=name, group="app")
            if first:
                widget.active = True
                self.ids.checkbox_app.selected = name
                first = False
            widget.bind(on_active=self.on_checkbox_app_active)
            self.ids.checkbox_app_layout.add_widget(widget)


    def _run_shell_cmd(self, cmd, wait = False):
        p = subprocess.Popen("su", executable=ANDROID_SHELL, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p.communicate(cmd+'\n')

        if wait:
            p.wait()
            return p.returncode
        else:
            return None


    def __check_diag_mode(self):
        """
        Check if diagnostic mode is enabled.
        """
        
        cmd = " test -e /dev/diag"
        res = self._run_shell_cmd(cmd, True)
        if res:
            return False
        else:
            self._run_shell_cmd("chmod 755 /dev/diag")
            return True
        
        # hasDiag = True
        # res = subprocess.check_output("ls /dev/diag", executable=ANDROID_SHELL, shell=True, stderr=subprocess.STDOUT)
        # if "No such file or directory" in str(res):
        #     print "MAIN: __check_diag_mode() res = false"
        #     hasDiag = False
        # else:
        #     print "MAIN: __check_diag_mode() res = true"

        # return hasDiag


    def __init_libs(self):
        """
        Initialize libs required by MobileInsight
        """

        libs_path = os.path.join(self._get_files_dir(), "data")

        libs = ["libglib-2.0.so",
                "libgmodule-2.0.so",
                "libgobject-2.0.so",
                "libgthread-2.0.so",
                "libwireshark.so",
                "libwiretap.so",
                "libwsutil.so"]

        cmd = ""

        for lib in libs:
            # if not os.path.isfile(os.path.join("/system/lib",lib)):
            if True:
                cmd = cmd + " cp " + os.path.join(libs_path, lib) + " /system/lib/; "
                cmd = cmd + " chmod 755 " + os.path.join("/system/lib", lib) + "; "
        

        # sym links for some libs
        libs_mapping = {"libwireshark.so": ["libwireshark.so.6", "libwireshark.so.6.0.1"],
                      "libwiretap.so": ["libwiretap.so.5", "libwiretap.so.5.0.1"],
                      "libwsutil.so": ["libwsutil.so.6", "libwsutil.so.6.0.0"]}

        for lib in libs_mapping:
            for sym_lib in libs_mapping[lib]:
                # if not os.path.isfile("/system/lib/"+sym_lib):
                if True:
                   cmd = cmd + " ln -s /system/lib/" + lib + " /system/lib/" + sym_lib + "; "
                   cmd = cmd + " chmod 755 /system/lib/" + sym_lib + "; " 

        # print cmd  # debug mode

        # bins
        exes = ["diag_revealer",
                "android_pie_ws_dissector",
                "android_ws_dissector"]
        for exe in exes:
            # if not os.path.isfile(os.path.join("/system/bin",exe)):
            if True:
                cmd = cmd + " cp " + os.path.join(libs_path, exe) + " /system/bin/; "
                cmd = cmd + " chmod 755 " + os.path.join("/system/bin/", exe) + "; "

        if cmd:
            # at least one lib should be copied
            cmd = "mount -o remount,rw /system; " + cmd
            self._run_shell_cmd(cmd)


    def _create_folder(self):
        cmd = "mkdir /sdcard/mobile_insight; "
        cmd = cmd + "mkdir /sdcard/mobile_insight/log; "
        cmd = cmd + "mkdir /sdcard/mobile_insight/cfg; "
        cmd = cmd + "mkdir /sdcard/mobile_insight/dbs; "
        cmd = cmd + "mkdir /sdcard/mobile_insight/apps; "
        self._run_shell_cmd(cmd)


    def _add_log_line(self, s):
        self.error_log += "\n"
        self.error_log += s


    def run_script_callback(self):
        no_error = True

        if no_error:
            try:
                filename = self.ids["filename"].text
                self._add_log_line("")
                self._add_log_line("execfile: %s" % filename)
                namespace = { "app_log": "" }
                execfile(filename, namespace)
                # Load the "app_log" variable from namespace and print it out
                self._add_log_line(namespace["app_log"])
            except:
                print str(traceback.format_exc())
                self._add_log_line(str(traceback.format_exc()))
                no_error = False

    def _get_cache_dir(self):
        return str(self.current_activity.getCacheDir().getAbsolutePath())


    def _get_files_dir(self):
        return str(self.current_activity.getFilesDir().getAbsolutePath())

    def on_checkbox_app_active(self, obj):
        for cb in self.ids.checkbox_app_layout.children:
            if cb.active:
                self.ids.checkbox_app.selected = cb.text

        # Yuanjie: try to load readme.txt
        app_path = self.app_list[self.ids.checkbox_app.selected][0]
        if os.path.exists(os.path.join(app_path, "readme.txt")):
            with open(os.path.join(app_path, "readme.txt"), 'r') as ff:
                self.error_log = self.ids.checkbox_app.selected + ": " + ff.read()
        else:
            self.error_log = self.ids.checkbox_app.selected + ": no descriptions."

        return True


    def stop_collection(self):
        ANDROID_SHELL = "/system/bin/sh"
        self.collecting = False

        # Find diag_mdlog process
        diag_procs = []
        pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
        for pid in pids:
            try:
                cmdline = open(os.path.join("/proc", pid, "cmdline"), "rb").read()
                if cmdline.startswith("diag_mdlog") or cmdline.startswith("/system/bin/diag_revealer"):
                    diag_procs.append(int(pid))
            except IOError:     # proc has been terminated
                continue

        if len(diag_procs) > 0:
            cmd2 = "kill " + " ".join([str(pid) for pid in diag_procs])
            self._run_shell_cmd(cmd2)


    def start_service(self, app_name):
        if platform == "android" and app_name in self.app_list:
            if self.service:
                self.stop_service() # stop the running service

            if not self.app_list[app_name][1]:
                #No UI: run as Android service
                from android import AndroidService
                self.error_log = "Running " + app_name + "..."
                self.service = AndroidService("MobileInsight is running...", app_name)
                self.service.start(self.app_list[app_name][0])   # app name
                # self.wakelock.acquire()
            else:
                #With UI: run code directly
                execfile(os.path.join(self.app_list[app_name][0],"main_ui.mi2app"))
            

    def stop_service(self):
        if self.service:
            self.service.stop()
            self.service = None
            self.error_log="Stopped"
            self.stop_collection()  # close ongoing collections
            # self.wakelock.release()


    def about(self):
        about_text = ('MobileInsight 2.0 \n' 
                   + 'UCLA WiNG Group & OSU MSSN Lab\n\n' 
                   + 'Developers:\n'
                   + '     Yuanjie Li,\n'
                   + '     Zengwen Yuan,\n'
                   + '     Jiayao Li,\n'
                   + '     Haotian Deng\n\n'
                   + 'Copyright © 2014 – 2016')
        popup = Popup(title='About MobileInsight',
                      content=Label(text=about_text),
                      size_hint=(.8, .4))
        popup.open()

class LabeledCheckBox(GridLayout):
    active = BooleanProperty(False)
    text = StringProperty("")
    group = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type("on_active")
        super(LabeledCheckBox, self).__init__(**kwargs)
        self.active = kwargs.get("active", False)
        self.text   = kwargs.get("text", False)
        self.group  = kwargs.get("group", None)

    def on_active(self, *args):
        pass
    
    def callback(self, cb, value):
        self.active = value
        self.dispatch("on_active")


class MobileInsightApp(App):
    screen = None

    def build_settings(self, settings):

        with open("settings.json", "r") as settings_json:
            settings.add_json_panel('General settings', self.config, data=settings_json.read())

        self.create_app_settings(self.config,settings)

    def create_app_settings(self,config,settings):
        app_list = get_app_list()
        for app in app_list:
            APP_NAME = app
            APP_DIR = app_list[app][0]
            setting_path = os.path.join(APP_DIR, "settings.json")
            if os.path.exists(setting_path):
                with open(setting_path, "r") as settings_json:
                    raw_data = settings_json.read()


                    # Regulate the config into the format that kivy can accept 
                    tmp = eval(raw_data)

                    result = "["
                    default_val={}

                    for index in range(len(tmp)):
                        if tmp[index]['type'] == 'title':
                            result =  result+'{"type": "title","title": ""},'
                        elif tmp[index]['type'] == 'options':
                            default_val[tmp[index]['key']]=tmp[index]['default']
                            result = result+'{"type": "'+tmp[index]['type'] \
                                   + '","title":"'+tmp[index]['title'] \
                                   + '","desc":"'+tmp[index]['desc'] \
                                   + '","section":"'+APP_NAME \
                                   + '","key":"'+tmp[index]['key'] \
                                   + '","options":'+json.dumps(tmp[index]['options']) \
                                   + '},'
                        else:
                            default_val[tmp[index]['key']]=tmp[index]['default']
                            result = result+'{"type": "'+tmp[index]['type'] \
                                   + '","title":"'+tmp[index]['title'] \
                                   + '","desc":"'+tmp[index]['desc'] \
                                   + '","section":"'+APP_NAME \
                                   + '","key":"'+tmp[index]['key'] \
                                   + '"},'
                    result = result[0:-1]+"]"

                    #Update the default value and setting menu
                    settings.add_json_panel(APP_NAME, config, data=result)

    def build_config(self, config):
        # Yuanjie: the ordering of the following options MUST be the same as those in settings.json!!!
        config.setdefaults('mi_section', {
            'bStartUp': True,
        })
        self.create_app_default_config(config)

    def create_app_default_config(self, config):
        app_list = get_app_list()
        for app in app_list:
            APP_NAME = app
            APP_DIR = app_list[app][0]
            setting_path = os.path.join(APP_DIR, "settings.json")
            if os.path.exists(setting_path):
                with open(setting_path, "r") as settings_json:
                    raw_data = settings_json.read()

                    # Regulate the config into the format that kivy can accept 
                    tmp = eval(raw_data)

                    default_val={}

                    for index in range(len(tmp)):
                        if tmp[index]['type'] == 'title':
                            pass
                        elif 'default' in tmp[index]:
                            default_val[tmp[index]['key']]=tmp[index]['default']

                    #Update the default value and setting menu
                    config.setdefaults(APP_NAME,default_val)



    def build(self):
        self.screen = MobileInsightScreen()
        Window.borderless = False
        return self.screen

    def on_pause(self):
        # Yuanjie: The following code prevents screen freeze when screen off -> screen on
        current_activity = cast("android.app.Activity",
                            autoclass("org.renpy.android.PythonActivity").mActivity)
        current_activity.moveTaskToBack(True)
        return True  # go into Pause mode

    def on_resume(self):
        pass

    def on_stop(self):
        self.screen.stop_service()


if __name__ == "__main__":
    MobileInsightApp().run()
