import kivy
kivy.require('1.0.9')

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

ANDROID_SHELL = "/system/bin/sh"

Window.softinput_mode = "pan"
Window.clearcolor = (1, 1, 1, 1)

Builder.load_string("""

<ScrollableLabel@ScrollView>:
    text: ''

    Label:
        text: root.text
        text_size: self.width, None
        size_hint_y: None
        font_size: "24sp"
        color: 0,0,0,1
        height: self.texture_size[1]
        valign: 'top'

<LabeledCheckBox@GridLayout>:
    cols: 2
    active: False
    text: ''
    group: None

    CheckBox:
        canvas.before:
            Color:
                rgba: 0,0,0,1
            Rectangle:
                pos: self.pos
                size: self.size
        active: root.active
        group: root.group
        size_hint_x: None
        font_size: "24sp"
        on_active: root.callback(*args)

    Label:
        canvas.before:
            Color:
                rgba: 0,0,0,1
            Rectangle:
                pos: self.pos
                size: self.size
        text: root.text
        font_size: "24sp"
        color: 1,1,1,1
        bcolor: 0,0,0,1
        text_width: self.width

# Main screen
<MobileInsightScreen>:
    cols: 1

    ScrollableLabel:
        text: '%s' % root.error_log
        size_hint_y: 6

    ScrollView:
        id: checkbox_app
        size_hint_y: 8
        font_size: "24sp"
        selected: ""

        BoxLayout:
            id: checkbox_app_layout
            orientation: 'vertical'

    Button:
        text: 'Run %s' % root.ids.checkbox_app.selected
        disabled: root.ids.checkbox_app.selected == ''
        size_hint_y: 2.5
        font_size: "24sp"
        on_release: root.start_service(root.ids.checkbox_app.selected)

    Button:
        text: 'Stop %s' % root.ids.checkbox_app.selected
        disabled: root.ids.checkbox_app.selected == ''
        size_hint_y: 2.5
        font_size: "24sp"
        on_release: root.stop_service()

    Button:
        text: 'About' 
        disabled: root.ids.checkbox_app.selected == ''
        size_hint_y: 2.5
        font_size: "24sp"
        on_release: root.about()

""")

class MobileInsightScreen(GridLayout):
    error_log = StringProperty("MobileInsight 2.0\nUCLA WiNG Group & OSU MSSN Lab")
    collecting = BooleanProperty(False)
    current_activity = cast("android.app.Activity",
                            autoclass("org.renpy.android.PythonActivity").mActivity)
    service = None
    analyzer = None

    def __init__(self):
        super(MobileInsightScreen, self).__init__()
        self.app_list = self._get_app_list()
        # self.app_list.sort()

        self.__init_libs()
        self._create_folder()

        if not self.__check_diag_mode():
            self.error_log = "WARINING: the diagnostic mode is disabled. Please check your phone settings."

        self.stop_collection()  # clean up ongoing log collections

        first = True
        for name in self.app_list:
            widget = LabeledCheckBox(text=name, group="app")
            if first:
                widget.active = True
                self.ids.checkbox_app.selected = name
                first = False
            widget.bind(on_active=self.on_checkbox_app_active)
            self.ids.checkbox_app_layout.add_widget(widget)

        # Init a wakelock for continuous MI service
        Context = autoclass('android.content.Context')
        PowerManager = autoclass('android.os.PowerManager')
        current_activity = cast("android.app.Activity",
                            autoclass("org.renpy.android.PythonActivity").mActivity)
        pm = current_activity.getSystemService(Context.POWER_SERVICE)
        self.wakelock = pm.newWakeLock(PowerManager.SCREEN_DIM_WAKE_LOCK, "MobileInsight");


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


    def _get_app_list(self):

        ret = {} # app_name->path

        APP_DIR = os.path.join(self._get_files_dir(), "app")
        l = os.listdir(APP_DIR)
        for f in l:
            if os.path.exists(os.path.join(APP_DIR, f, "main.mi2app")):
                # ret.append(f)
                ret[f] = os.path.join(APP_DIR, f)

        # Yuanjie: support alternative path for users to customize their own app
        APP_DIR = "/sdcard/mobile_insight/apps/"
        if os.path.exists(APP_DIR):
            l = os.listdir(APP_DIR)
            for f in l:
                if os.path.exists(os.path.join(APP_DIR, f, "main.mi2app")):
                    if f in ret:
                        tmp_name = f + " (plugin)"
                    else:
                        tmp_name = f
                    ret[tmp_name] = os.path.join(APP_DIR, f)
        else: # create directory for user-customized apps
            cmd = "mkdir \"%s\";" % APP_DIR
            self._run_shell_cmd(cmd)

        return ret


    def on_checkbox_app_active(self, obj):
        for cb in self.ids.checkbox_app_layout.children:
            if cb.active:
                self.ids.checkbox_app.selected = cb.text

        # Yuanjie: try to load readme.txt
        app_path = self.app_list[self.ids.checkbox_app.selected]
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
            from android import AndroidService
            self.error_log = "Running " + app_name + "..."
            self.service = AndroidService("MobileInsight is running...", app_name)
            self.service.start(self.app_list[app_name])   # app name
            self.wakelock.acquire()
            

    def stop_service(self):
        if self.service:
            self.service.stop()
            self.service = None
            self.error_log="Stopped"
            self.stop_collection()  # close ongoing collections
            self.wakelock.release()


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

    def build(self):
        self.screen = MobileInsightScreen()
        return self.screen

    def on_pause(self):
        return True  # go into Pause mode

    def on_stop(self):
        self.screen.stop_service()


if __name__ == "__main__":
    MobileInsightApp().run()
