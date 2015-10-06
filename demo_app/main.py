import kivy
kivy.require('1.0.9')

from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import *

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder

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

# Main screen
<HelloWorldScreen>:
    cols: 1

    ScrollableLabel:
        text: '%s' % root.error_log
        size_hint_y: 18

    TextInput:
        id: filename
        size_hint_y: 3
        text: '/sdcard/execfile_test.py'
        multiline: False

    Button:
        text: 'Run script!'
        size_hint_y: 4
        on_release: root.my_callback()

    Button:
        text: 'Start collection'
        disabled: root.collecting
        size_hint_y: 4
        on_release: root.start_collection()

    Button:
        text: 'Stop collection'
        disabled: not root.collecting
        size_hint_y: 4
        on_release: root.stop_collection()
""")

class HelloWorldScreen(GridLayout):
    error_log = StringProperty("Nico-Nico-Ni!")
    collecting = BooleanProperty(False)
    qmdl_src = None
    analyzer = None

    def __init__(self):
        super(HelloWorldScreen, self).__init__()

    def _add_log_line(self, s):
        self.error_log += "\n"
        self.error_log += s

    def my_callback(self):
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
                # self._add_log_line(repr(namespace))
                self._add_log_line(namespace["app_log"])
            except:
                self._add_log_line(str(traceback.format_exc()))
                no_error = False

    def start_collection(self):
        # The subprocess module uses "/bin/sh" by default, which must be changed on Android.
        # See http://grokbase.com/t/gg/python-for-android/1343rm7q1w/py4a-subprocess-popen-oserror-errno-8-exec-format-error
        ANDROID_SHELL = "/system/bin/sh"
        LOG_DIR = "/sdcard/external_sd/mobile_insight_log"

        def clock_callback(infos, dt):
            if not self.collecting:
                self._add_log_line("Stop")
                return False    # Cancel it

            qmdls_after = set(os.listdir(LOG_DIR))
            log_files = sorted(list(qmdls_after - infos["qmdls_before"]))
            for log_file in log_files:
                self._add_log_line("=== %s ===" % log_file)
                self.qmdl_src.set_input_path(os.path.join(LOG_DIR, log_file))
                self.analyzer.set_source(self.qmdl_src)
                self.qmdl_src.run()

            if self.analyzer.get_cur_cell():
                t = (self.analyzer.get_cur_cell().rat, self.analyzer.get_cur_cell().id)
                self._add_log_line(repr(t))
            infos["qmdls_before"] = qmdls_after

        cmd1 = "su -c diag_mdlog -s 1 -o \"%s\"" % LOG_DIR
        subprocess.Popen(cmd1, executable=ANDROID_SHELL, shell=True)

        from mobile_insight.monitor import QmdlReplayer
        from mobile_insight.analyzer import RrcAnalyzer
        self.qmdl_src = QmdlReplayer({  "ws_dissect_executable_path": "/data/ws_dissector/android_pie_ws_dissector",
                                        "libwireshark_path": "/data/ws_dissector/"})
        self.analyzer = RrcAnalyzer()

        infos = {
            "qmdls_before": set(os.listdir(LOG_DIR)),
        }
        self.collecting = True
        Clock.schedule_interval(functools.partial(clock_callback, infos), 1)


    def stop_collection(self):
        self.collecting = False

        # Find diag_mdlog process
        diag_procs = []
        pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
        for pid in pids:
            try:
                cmdline = open(os.path.join("/proc", pid, "cmdline"), "rb").read()
                if cmdline.startswith("diag_mdlog"):
                    diag_procs.append(int(pid))
            except IOError:
                continue

        if len(diag_procs) > 0:
            cmd2 = "su -c kill -9 " + " ".join([str(pid) for pid in diag_procs])
            subprocess.Popen(cmd2, executable=ANDROID_SHELL, shell=True)


class HelloWorldApp(App):
    def build(self):
        return HelloWorldScreen()


if __name__ == "__main__":
    ANDROID_SHELL = "/system/bin/sh"
    cmd = "su -c echo hello"
    subprocess.Popen(cmd, executable=ANDROID_SHELL, shell=True)

    HelloWorldApp().run()
