__version__ = "0.1"

import kivy
kivy.require('1.0.9')

from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
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

# Prevent Android on-screen keyboard from hiding text input
# See http://stackoverflow.com/questions/26799084/android-on-screen-keyboard-hiding-python-kivy-textinputs
Window.softinput_mode = "pan"

Builder.load_string("""
# A scrollable label class.
# Taken from http://tune.pk/video/2639621/kivy-crash-course-9-creating-a-scrollable-label
<ScrollableLabel@ScrollView>:
    text: ''

    Label:
        text: root.text
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1]
        valign: 'top'

<LabeledCheckBox@GridLayout>:
    cols: 2
    active: False
    text: ''
    group: None

    CheckBox:
        active: root.active
        group: root.group
        size_hint_x: None
        on_active: root.callback(*args)

    Label:
        text: root.text
        text_width: self.width

# Main screen
<HelloWorldScreen>:
    cols: 1

    ScrollableLabel:
        text: '%s' % root.error_log
        size_hint_y: 10

    TextInput:
        id: filename
        size_hint_y: 3
        text: '/sdcard/execfile_test.py'
        multiline: False

    Button:
        text: 'Run script!'
        size_hint_y: 4
        on_release: root.run_script_callback()

    ScrollView:
        id: checkbox_app
        size_hint_y: 10
        selected: ""

        BoxLayout:
            id: checkbox_app_layout
            orientation: 'vertical'

    Button:
        text: 'Run app! %s' % root.ids.checkbox_app.selected
        disabled: root.ids.checkbox_app.selected == ''
        size_hint_y: 4
        on_release: root.start_service(root.ids.checkbox_app.selected)

    Button:
        text: 'Start collection'
        disabled: root.collecting
        size_hint_y: 4
        on_release: root.start_collection()

    Button:
        text: 'Stop collection'
        size_hint_y: 4
        on_release: root.stop_collection()
""")

class HelloWorldScreen(GridLayout):
    error_log = StringProperty("Nico-Nico-Ni!")
    collecting = BooleanProperty(False)
    current_activity = cast("android.app.Activity",
                            autoclass("org.renpy.android.PythonActivity").mActivity)
    service = None
    qmdl_src = None
    analyzer = None

    def __init__(self):
        super(HelloWorldScreen, self).__init__()
        app_list = self._get_app_list()
        app_list.sort()

        first = True
        for name in app_list:
            widget = LabeledCheckBox(text=name, group="app")
            if first:
                widget.active = True
                self.ids.checkbox_app.selected = name
                first = False
            widget.bind(on_active=self.on_checkbox_app_active)
            self.ids.checkbox_app_layout.add_widget(widget)


    def _add_log_line(self, s):
        self.error_log += "\n"
        self.error_log += s

    def run_script_callback(self):
        no_error = True
        if no_error:
            try:
                import mobile_insight
                # self._add_log_line("Imported mobile_insight")
            except:
                self._add_log_line(str(traceback.format_exc()))
                no_error = False
        
        if no_error:
            try:
                import mobile_insight.monitor.dm_collector.dm_collector_c as dm_collector_c
                # self._add_log_line("Loaded dm_collector_c v%s" % dm_collector_c.version)
            except:
                self._add_log_line("Failed to load dm_collector_c")
                no_error = False

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
                self._add_log_line(str(traceback.format_exc()))
                no_error = False

    def _get_cache_dir(self):
        return str(self.current_activity.getCacheDir().getAbsolutePath())

    def _get_files_dir(self):
        return str(self.current_activity.getFilesDir().getAbsolutePath())

    def _get_app_list(self):
        APP_DIR = os.path.join(self._get_files_dir(), "app")
        l = os.listdir(APP_DIR)
        ret = []
        for f in l:
            if os.path.exists(os.path.join(APP_DIR, f, "main.mi2app")):
                ret.append(f)
        return ret

    def on_checkbox_app_active(self, obj):
        self.ids.checkbox_app.selected = ""
        for cb in self.ids.checkbox_app_layout.children:
            if cb.active:
                self.ids.checkbox_app.selected = cb.text
        return True

    def start_collection(self):
        # The subprocess module uses "/bin/sh" by default, which must be changed on Android.
        # See http://grokbase.com/t/gg/python-for-android/1343rm7q1w/py4a-subprocess-popen-oserror-errno-8-exec-format-error
        ANDROID_SHELL = "/system/bin/sh"
        LOG_DIR = self._get_cache_dir() + "/mobile_insight_log"
        self._add_log_line("LOG_DIR: %s" % LOG_DIR)

        def clock_callback(infos, dt):
            if not self.collecting:
                self._add_log_line("Stop")
                return False    # Cancel it

            qmdls_after = set(os.listdir(LOG_DIR))
            log_files = sorted(list(qmdls_after - infos["qmdls_before"]))
            for log_file in [l for l in log_files if l.endswith(".qmdl")]:
                self._add_log_line("=== %s ===" % log_file)
                self.qmdl_src.set_input_path(os.path.join(LOG_DIR, log_file))
                self.analyzer.set_source(self.qmdl_src)
                self.qmdl_src.run()

            if self.analyzer.get_cur_cell():
                t = (self.analyzer.get_cur_cell().rat, self.analyzer.get_cur_cell().id)
                self._add_log_line(repr(t))
            infos["qmdls_before"] = qmdls_after

        cmd = "su -c mkdir \"%s\"" % LOG_DIR
        subprocess.Popen(cmd, executable=ANDROID_SHELL, shell=True)
        cmd = "su -c chmod -R 777 \"%s\"" % LOG_DIR
        subprocess.Popen(cmd, executable=ANDROID_SHELL, shell=True)
        cmd = "su -c diag_mdlog -s 1 -o \"%s\"" % LOG_DIR
        subprocess.Popen(cmd, executable=ANDROID_SHELL, shell=True)

        from mobile_insight.monitor import QmdlReplayer
        from mobile_insight.analyzer import RrcAnalyzer
        self.qmdl_src = QmdlReplayer({  "ws_dissect_executable_path": "/system/bin/android_pie_ws_dissector",
                                        "libwireshark_path": "/system/lib"})
        self.analyzer = RrcAnalyzer()

        infos = {
            "qmdls_before": set(os.listdir(LOG_DIR)),
        }
        self.collecting = True
        Clock.schedule_interval(functools.partial(clock_callback, infos), 1)

    def stop_collection(self):
        ANDROID_SHELL = "/system/bin/sh"
        self.collecting = False

        # Find diag_mdlog process
        diag_procs = []
        pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
        for pid in pids:
            try:
                cmdline = open(os.path.join("/proc", pid, "cmdline"), "rb").read()
                if cmdline.startswith("diag_mdlog"):
                    diag_procs.append(int(pid))
            except IOError:     # proc has been terminated
                continue

        if len(diag_procs) > 0:
            cmd2 = "su -c kill " + " ".join([str(pid) for pid in diag_procs])
            subprocess.Popen(cmd2, executable=ANDROID_SHELL, shell=True)

    def start_service(self, app_name):
        if platform == "android" and app_name:
            from android import AndroidService
            service = AndroidService("Test service", "Running")
            service.start(app_name)   # app name
            self.service = service

    def stop_service(self):
        if self.service:
            self.service.stop()
            self.service = None


class LabeledCheckBox(GridLayout):
    active = BooleanProperty(False)
    text = StringProperty("")
    group = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type("on_active")
        super(LabeledCheckBox, self).__init__(**kwargs)
        self.active = kwargs.get("active", False)
        self.text = kwargs.get("text", False)
        self.group = kwargs.get("group", None)

    def on_active(self, *args):
        pass
    
    def callback(self, cb, value):
        self.active = value
        self.dispatch("on_active")


class HelloWorldApp(App):
    screen = None

    def build(self):
        self.screen = HelloWorldScreen()
        return self.screen

    def on_pause(self):
        return True     # go into Pause mode

    def on_stop(self):
        self.screen.stop_service()


if __name__ == "__main__":
    HelloWorldApp().run()
