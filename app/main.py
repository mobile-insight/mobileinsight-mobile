from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.text import Label as CoreLabel
from kivy.uix.button import Button
from kivy.properties import *
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import platform
from kivy.config import ConfigParser

from android import AndroidService
from jnius import autoclass, cast
import jnius

import functools
import os
import shlex
import sys
import subprocess
import threading
import time
import traceback
import re
import datetime
import shutil
import stat
import json

import main_utils
from log_viewer_app import LogViewerScreen

from collections import deque

# Load main UI
Window.softinput_mode = "pan"
Window.clearcolor = (1, 1, 1, 1)
Builder.load_file('main_ui.kv')
current_activity = cast("android.app.Activity", autoclass(
    "org.renpy.android.PythonActivity").mActivity)

LOGO_STRING = "MobileInsight " + main_utils.get_cur_version() + \
    "\nCopyright (c) 2015-2017 MobileInsight Team"


def create_folder():

    cmd = ""

    mobileinsight_path = main_utils.get_mobileinsight_path()
    if not mobileinsight_path:
        return False

    try:
        legacy_mobileinsight_path = main_utils.get_legacy_mobileinsight_path()
        cmd = cmd + "mv " + legacy_mobileinsight_path + " " + mobileinsight_path + "; "
        cmd = cmd + "mv " + legacy_mobileinsight_path + "/apps/ " + mobileinsight_path + "/plugins/; "
    except:
        pass

    if not os.path.exists(mobileinsight_path):
        cmd = cmd + "mkdir " + mobileinsight_path + "; "
        cmd = cmd + "chmod -R 755 " + mobileinsight_path + "; "


    log_path = main_utils.get_mobileinsight_log_path()
    if not os.path.exists(log_path):
        cmd = cmd + "mkdir " + log_path + "; "
        cmd = cmd + "chmod -R 755 " + log_path + "; "

    analysis_path = main_utils.get_mobileinsight_analysis_path()
    if not os.path.exists(analysis_path):
        cmd = cmd + "mkdir " + analysis_path + "; "
        cmd = cmd + "chmod -R 755 " + analysis_path + "; "

    cfg_path = main_utils.get_mobileinsight_cfg_path()
    if not os.path.exists(analysis_path):
        cmd = cmd + "mkdir " + cfg_path + "; "
        cmd = cmd + "chmod -R 755 " + cfg_path + "; "

    db_path = main_utils.get_mobileinsight_db_path()
    if not os.path.exists(db_path):
        cmd = cmd + "mkdir " + db_path + "; "
        cmd = cmd + "chmod -R 755 " + db_path + "; "

    plugin_path = main_utils.get_mobileinsight_plugin_path()
    if not os.path.exists(plugin_path):
        cmd = cmd + "mkdir " + plugin_path + "; "
        cmd = cmd + "chmod -R 755 " + plugin_path + "; "

    log_decoded_path = main_utils.get_mobileinsight_log_decoded_path()
    if not os.path.exists(log_decoded_path):
        cmd = cmd + "mkdir " + log_decoded_path + "; "
        cmd = cmd + "chmod -R 755 " + log_decoded_path + "; "

    log_uploaded_path = main_utils.get_mobileinsight_log_uploaded_path()
    if not os.path.exists(log_uploaded_path):
        cmd = cmd + "mkdir " + log_uploaded_path + "; "
        cmd = cmd + "chmod -R 755 " + log_uploaded_path + "; "

    crash_log_path = main_utils.get_mobileinsight_crash_log_path()
    if not os.path.exists(crash_log_path):
        cmd = cmd + "mkdir " + crash_log_path + "; "
        cmd = cmd + "chmod -R 755 " + crash_log_path + "; "

    # cmd = cmd + "chmod -R 755 "+mobileinsight_path+"; "

    main_utils.run_shell_cmd(cmd)
    return True


def get_plugins_list():
    '''
    Load plugin lists, including both built-in and 3rd-party plugins
    '''

    ret = {}  # app_name->(path,with_UI)

    APP_DIR = os.path.join(
        str(current_activity.getFilesDir().getAbsolutePath()), "plugins")
    l = os.listdir(APP_DIR)
    for f in l:
        if os.path.exists(os.path.join(APP_DIR, f, "main.mi2app")):
            # ret.append(f)
            ret[f] = (os.path.join(APP_DIR, f), False)

    # Yuanjie: support alternative path for users to customize their own plugin
    APP_DIR = main_utils.get_mobileinsight_plugin_path()

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
    else:  # create directory for user-customized apps
        create_folder()
    
    return ret

# class MobileInsightScreen(GridLayout):

class MobileInsightScreen(Screen):
    error_log = StringProperty(LOGO_STRING)
    default_app_name = StringProperty("")
    collecting = BooleanProperty(False)
    service = None
    analyzer = None
    terminal_thread = None
    terminal_stop = None
    MAX_LINE = 30
    logs = deque([],MAX_LINE)
    plugins = []
    selectedPlugin = ""
    myLayout = GridLayout(cols = 2, spacing = 5, orientation = "vertical", size_hint_y = None, height = (len(get_plugins_list())/2+len(get_plugins_list())%2)*Window.height/4)
    popupScroll = ScrollView(size_hint_y = None, size = (Window.width, Window.height*.9))
    popupScroll.add_widget(myLayout)
    popup = Popup(content = popupScroll, title = "Choose a plugin")
    def __init__(self, name):
        """
        Initialization function. We will do the following task (in order):
            1. Check if the device is rooted
            2. Initialize necessary libs required by MobileInsight (e.g., libwireshark)
            3. Check if Android's security policy allows MobileInsight to access diagnostic mode.
            This is mainly caused by SELinux
            4. Create necessary folders on SDcard (e.g., /sdcard/mobileinsight/, /sdcard/mobileinsight/log/)
            5. Load built-in and 3rd-party plugins (located in /sdcard/mobileinsight/plugins/)
            6. Check if the diagnostic mode is enabled
            7. Load configurations from the setting panel (configs stored in /sdcard/.mobileinsight.ini)
        """

        super(MobileInsightScreen, self).__init__()

        self.name = name

        if not main_utils.is_rooted():
            # self.ids.log_viewer.disabled = False
            # self.ids.run_plugin.disabled = False
            self.log_error(
                "MobileInsight requires root privilege. Please root your device for correct functioning.")

        
        self.__init_libs()
        self.__check_security_policy()

        if not create_folder():
            # MobileInsight folders unavailable. Add warnings
            self.log_error("SDcard is unavailable. Please check.")
            self.screen.ids.log_viewer.disabled = True
            self.screen.ids.stop_plugin.disabled = True
            self.screen.ids.run_plugin.disabled = True

        self.plugins_list = get_plugins_list()
        # self.plugins_list.sort()

        if not self.__check_diag_mode():
            self.log_error(
                "The diagnostic mode is disabled. Please check your phone settings.")

        # clean up ongoing log collections
        # self.stop_collection()

        self.terminal_stop = None
        self.terminal_thread = None
        bootup = True

        #used to shorten long widget names in popup menu
        shortenLabel = CoreLabel(markup = True, text_size = (Window.width/2.5, None), shorten_from = "right", font_size = 70)
        #Making and adding widgets to popup menu
        for name in self.plugins_list:
            widget = Button(id = name, markup = True, halign = "left", valign = "top", on_release = self.callback, background_normal = "", background_color = self.ids.run_plugin.background_color)
            widget.text_size = (Window.width/2.25, Window.height/4)
            self.myLayout.add_widget(widget)

            app_path = self.plugins_list[name][0]
            if os.path.exists(os.path.join(app_path, "readme.txt")):
                with open(os.path.join(app_path, "readme.txt"), 'r') as ff:
                    my_description = ff.read()
            else: 
                my_description = "no description."
            #shortening long widget names and making font size
            shortenedName = shortenLabel.shorten(name)
            font_size = "60"
            if Window.width < 1450:
                font_size = "45"
            widget.text = "[color=fffafa][size=70]"+ shortenedName + "[/size][size="+ font_size + "]\n"+ my_description+"[/size][/color]"

            if bootup:
                self.selectedPlugin = name
                self.ids.selectButton.text = "Select Plugin"
                self.ids.run_plugin.text  = "Run Plugin: "+self.selectedPlugin
                bootup = False
        # If default service exists, launch it
        try:
            config = ConfigParser()
            config.read('/sdcard/.mobileinsight.ini')
            default_app_name = config.get("mi_general", "start_service")
            launch_service = config.get("mi_general", "bstartup_service")
            if default_app_name and launch_service == "1":
                self.start_service(default_app_name)
                self.ids.run_plugin.text = "Stop Plugin: "+default_app_name
        except Exception as e:
            pass

    #Setting the text for the Select Plugin Menu button
    def callback(self, obj):
        self.selectedPlugin = obj.id
        # self.ids.selectButton.text = "Select Button: " + obj.text[(obj.text.find("]", obj.text.find("]")+1)+1):obj.text.find("[", obj.text.find("[", obj.text.find("[")+1)+1)]
        self.ids.selectButton.text = "Select Plugin"
        if not self.service:
            self.ids.run_plugin.text  = "Run Plugin: "+self.selectedPlugin
        self.popup.dismiss()
        

    def log_info(self, msg):
        self.append_log("[b][color=00ff00][INFO][/color][/b]: " + msg)

    def log_warning(self, msg):
        self.append_log("[b][color=00ffff][WARNING][/color][/b]: " + msg)

    def log_error(self, msg):
        self.append_log("[b][color=ff0000][ERROR][/color][/b]: " + msg)

    def append_log(self, s):
        self.error_log += "\n"
        self.error_log += s

    # def append_log(self,s):
    #     self.error_log += "\n"
    #     self.error_log += s
    #     if self.line_count > self.MAX_LINE:
    #         idx = self.error_log.find('\n')
    #         self.error_log = self.error_log[idx+1:]
    #     else:
    #         self.line_count += 1

    def __check_security_policy(self):
        """
        Update SELinux policy.
        For Nexus 6/6P, the SELinux policy may forbids the log collection.
        """

        cmd = "setenforce 0; "

        cmd = cmd + "supolicy --live \"allow init logd dir getattr\";"

        # # Depreciated supolicies. Still keep them for backup purpose
        cmd = cmd + "supolicy --live \"allow init init process execmem\";"
        cmd = cmd + \
            "supolicy --live \"allow atfwd diag_device chr_file {read write open ioctl}\";"
        cmd = cmd + "supolicy --live \"allow init properties_device file execute\";"
        cmd = cmd + \
            "supolicy --live \"allow system_server diag_device chr_file {read write}\";"

        # # Suspicious supolicies: MI works without them, but it seems that they SHOULD be enabled...

        # # mi2log permission denied (logcat | grep denied), but no impact on log collection/analysis
        cmd = cmd + \
            "supolicy --live \"allow untrusted_app app_data_file file {rename}\";"

        # # Suspicious: why still works after disabling this command? Won't FIFO fail?
        cmd = cmd + \
            "supolicy --live \"allow init app_data_file fifo_file {write open getattr}\";"
        cmd = cmd + \
            "supolicy --live \"allow init diag_device chr_file {getattr write ioctl}\"; "

        # Nexus 6 only
        cmd = cmd + \
            "supolicy --live \"allow untrusted_app diag_device chr_file {write open getattr}\";"
        cmd = cmd + \
            "supolicy --live \"allow system_server diag_device chr_file {read write}\";"
        cmd = cmd + \
            "supolicy --live \"allow netmgrd diag_device chr_file {read write}\";"
        cmd = cmd + \
            "supolicy --live \"allow rild diag_device chr_file {read write}\";"
        cmd = cmd + \
            "supolicy --live \"allow rild debuggerd app_data_file {read open getattr}\";"

        main_utils.run_shell_cmd(cmd)

    def __check_diag_mode(self):
        """
        Check if diagnostic mode is enabled.
        Note that this function is chipset-specific: Qualcomm and MTK have different detection approaches
"""
        chipset_type = main_utils.get_chipset_type()
        if chipset_type == main_utils.ChipsetType.QUALCOMM:
            diag_port = "/dev/diag"
            if not os.path.exists(diag_port):
                return False
            else:
                main_utils.run_shell_cmd("chmod 777 /dev/diag")
                return True
        elif chipset_type == main_utils.ChipsetType.MTK:
            cmd = "ps | grep emdlogger1"
            res = main_utils.run_shell_cmd(cmd)
            if not res:
                return False
            else:
                return True

    def __init_libs(self):
        """
        Initialize libs required by MobileInsight.
        It creates sym links to libs, and chmod of critical execs
        """

        libs_path = os.path.join(main_utils.get_files_dir(), "data")
        cmd = ""

        libs_mapping = {
            "libwireshark.so": [
                "libwireshark.so.6", "libwireshark.so.6.0.1"], "libwiretap.so": [
                "libwiretap.so.5", "libwiretap.so.5.0.1"], "libwsutil.so": [
                "libwsutil.so.6", "libwsutil.so.6.0.0"]}
        for lib in libs_mapping:
            for sym_lib in libs_mapping[lib]:
                # if not os.path.isfile(os.path.join(libs_path,sym_lib)):
                if True:
                    cmd = cmd + " ln -s " + \
                        os.path.join(libs_path, lib) + " " + os.path.join(libs_path, sym_lib) + "; "

        exes = ["diag_revealer",
                "diag_revealer_mtk",
                "android_pie_ws_dissector",
                "android_ws_dissector"]
        for exe in exes:
            cmd = cmd + " chmod 0755 " + os.path.join(libs_path, exe) + "; "

        cmd = cmd + "chmod -R 755 " + libs_path
        main_utils.run_shell_cmd(cmd)

    # def __init_libs(self):
    #     """
    #     Initialize libs required by MobileInsight
    #     """

    #     libs_path = os.path.join(main_utils.get_files_dir(), "data")

    #     libs = ["libglib-2.0.so",
    #             "libgmodule-2.0.so",
    #             "libgobject-2.0.so",
    #             "libgthread-2.0.so",
    #             "libwireshark.so",
    #             "libwiretap.so",
    #             "libwsutil.so"]

    #     cmd = "mount -o remount,rw /system; "

    #     for lib in libs:
    #         # if not os.path.isfile(os.path.join("/system/lib",lib)):
    #         if True:
    #             cmd = cmd + " cp " + os.path.join(libs_path, lib) + " /system/lib/; "
    #             cmd = cmd + " chmod 755 " + os.path.join("/system/lib", lib) + "; "

    #     # sym links for some libs
    #     libs_mapping = {"libwireshark.so": ["libwireshark.so.6", "libwireshark.so.6.0.1"],
    #                   "libwiretap.so": ["libwiretap.so.5", "libwiretap.so.5.0.1"],
    #                   "libwsutil.so": ["libwsutil.so.6", "libwsutil.so.6.0.0"]}

    #     for lib in libs_mapping:
    #         for sym_lib in libs_mapping[lib]:
    #             # if not os.path.isfile("/system/lib/"+sym_lib):
    #             if True:
    #                cmd = cmd + " ln -s /system/lib/" + lib + " /system/lib/" + sym_lib + "; "
    #                cmd = cmd + " chmod 755 /system/lib/" + sym_lib + "; "

    #     # print cmd  # debug mode

    #     # bins
    #     exes = ["diag_revealer",
    #             "android_pie_ws_dissector",
    #             "android_ws_dissector"]
    #     for exe in exes:
    #         # if not os.path.isfile(os.path.join("/system/bin",exe)):
    #         if True:
    #             cmd = cmd + " cp " + os.path.join(libs_path, exe) + " /system/bin/; "
    #             # 0755, not 755. "0" means "+x" on Android phones
    #             cmd = cmd + " chmod 0755 " + os.path.join("/system/bin/", exe) + "; "

    #     if cmd:
    #         # at least one lib should be copied
    #         main_utils.run_shell_cmd(cmd)

    def show_log(self):

        while not os.path.exists(self.log_name):
            continue

        log_file = open(self.log_name, 'r')

        # line_count = 0

        while True:
            if self.terminal_stop.is_set():
                continue
            try:
                time.sleep(1)
                where = log_file.tell()
                lines = log_file.readlines()
                if not lines:
                    log_file.seek(where)
                else:    
                    self.logs += lines
                    self.error_log = ''.join(self.logs)
            except Exception as e:
                import traceback
                print str(traceback.format_exc())
                continue

    def run_script_callback(self):
        no_error = True

        if no_error:
            try:
                filename = self.ids["filename"].text
                self.append_log("")
                self.append_log("execfile: %s" % filename)
                namespace = {"app_log": ""}
                execfile(filename, namespace)
                # Load the "app_log" variable from namespace and print it out
                self.append_log(namespace["app_log"])
            except BaseException:
                print str(traceback.format_exc())
                self.append_log(str(traceback.format_exc()))
                no_error = False


    def stop_collection(self):
        res = main_utils.run_shell_cmd("ps").split('\n')
        for item in res:
            if item.find('diag_revealer') != -1:
                pid = item.split()[1]
                cmd = "kill "+pid
                main_utils.run_shell_cmd(cmd)

    """
    def stop_collection(self):
        self.collecting = False

        # Find diag_revealer process
        # FIXME: No longer work for 7.0: os.listdir() only returns current
        # processstop_collection
        diag_procs = []
        pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
        print "stop_collection", str(pids)
        for pid in pids:
            try:
                cmdline = open(
                    os.path.join(
                        "/proc",
                        pid,
                        "cmdline"),
                    "rb").read()
                # if cmdline.startswith("diag_mdlog") or
                # cmdline.startswith("diag_revealer"):
                if cmdline.find("diag_revealer") != - \
                        1 or cmdline.find("diag_mdlog") != -1:
                    diag_procs.append(int(pid))
            except IOError:     # proc has been terminated
                continue
        if len(diag_procs) > 0:
            cmd2 = "kill " + " ".join([str(pid) for pid in diag_procs])
            main_utils.run_shell_cmd(cmd2)
    """

    def popUpMenu(self):
        self.popup.open()

    def start_service(self, app_name):
        if platform == "android" and app_name in self.plugins_list:
            # Clean up old logs
            self.log_name = os.path.join(
                main_utils.get_mobileinsight_analysis_path(),
                app_name + "_log.txt")
            if os.path.exists(self.log_name):
                os.remove(self.log_name)

            self.terminal_stop = threading.Event()
            self.terminal_thread = threading.Thread(target=self.show_log)
            self.terminal_thread.start()

            self.error_log = "Running " + app_name + "..."
            self.service = AndroidService(
                "MobileInsight is running...", app_name)
            
            # stop the running service
            self.service.stop()

            self.service.start(
                app_name + ":" + self.plugins_list[app_name][0])   # app name
            self.default_app_name = app_name

        else:
            self.error_log = "Error: " + app_name + "cannot be launched!"

    def stop_service(self):
        if self.service:
            self.service.stop()
            self.service = None
            if self.terminal_stop:
                self.terminal_stop.set()
            # self.error_log = LOGO_STRING
            self.log_info(
                "Plugin stopped. Detailed analytic results are saved in " +
                self.log_name)

            self.stop_collection()  # close ongoing collections

            # Haotian: save orphan log
            dated_files = []
            self.__logdir = main_utils.get_mobileinsight_log_path()
            self.__phone_info = main_utils.get_phone_info()
            mi2log_folder = os.path.join(main_utils.get_cache_dir(), "mi2log")
            for subdir, dirs, files in os.walk(mi2log_folder):
                for f in files:
                    fn = os.path.join(subdir, f)
                    dated_files.append((os.path.getmtime(fn), fn))
            dated_files.sort()
            dated_files.reverse()
            if len(dated_files) > 0:
                self.__original_filename = dated_files[0][1]
                # print "The last orphan log file: " +
                # str(self.__original_filename)
                chmodcmd = "chmod 644 " + self.__original_filename
                p = subprocess.Popen(
                    "su ",
                    executable=main_utils.ANDROID_SHELL,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE)
                p.communicate(chmodcmd + '\n')
                p.wait()
                self._save_log()

    def on_click_plugin(self, app_name):
        if self.service:
            self.stop_service()
            self.ids.run_plugin.text = "Run Plugin: "+app_name
        else:
            self.start_service(app_name)
            self.ids.run_plugin.text = "Stop Plugin: "+app_name

    def _save_log(self):
        orig_basename = os.path.basename(self.__original_filename)
        orig_dirname = os.path.dirname(self.__original_filename)
        self.__log_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        milog_basename = "diag_log_%s_%s_%s.mi2log" % (
            self.__log_timestamp, self.__phone_info, main_utils.get_operator_info())
        milog_absname = os.path.join(self.__logdir, milog_basename)
        main_utils.run_shell_cmd("cp %s %s" %
                                   (self.__original_filename, milog_absname))
        # shutil.copyfile(self.__original_filename, milog_absname)
        # chmodcmd = "rm -f " + self.__original_filename
        # p = subprocess.Popen("su ", executable = main_utils.ANDROID_SHELL, shell = True, \
        #                             stdin = subprocess.PIPE, stdout = subprocess.PIPE)
        # p.communicate(chmodcmd + '\n')
        # p.wait()
        os.remove(self.__original_filename)

    def about(self):
        about_text = ('MobileInsight ' + main_utils.get_cur_version() + ' \n'
                      + 'MobileInsight Team\n\n'
                      + 'Developers:\n'
                      + '    Yuanjie Li,\n'
                      + '    Zengwen Yuan,\n'
                      + '    Jiayao Li,\n'
                      + '    Haotian Deng\n\n'
                      + 'Copyright (c) 2014 – 2017')
        popup = Popup(title='About MobileInsight',
                      size_hint=(1,1),
                      background = "gradient.png"
                     )
        popup_button = Button(text = about_text, background_color = [0,0,0,0], on_press = popup.dismiss)
        popup.content = popup_button
        popup.open()


#class LabeledCheckBox(GridLayout):
#    active = BooleanProperty(False)
#    text = StringProperty("")
#    group = ObjectProperty(None, allownone=True)

#    def __init__(self, **kwargs):
#        self.register_event_type("on_active")
#        super(LabeledCheckBox, self).__init__(**kwargs)
#        self.active = kwargs.get("active", False)
#        self.text = kwargs.get("text", False)
#        self.group = kwargs.get("group", None)

#    def on_active(self, *args):
#        pass

#    def callback(self, cb, value):
#        self.active = value
#        self.dispatch("on_active")
  
class MobileInsightApp(App):
    screen = None
    use_kivy_settings = False
    log_viewer = None

    def build_settings(self, settings):

        with open("settings.json", "r") as settings_json:
            settings.add_json_panel(
                'General', self.config, data=settings_json.read())

        self.create_app_settings(self.config, settings)

    def create_app_settings(self, config, settings):
        app_list = get_plugins_list()
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
                    default_val = {}

                    for index in range(len(tmp)):
                        if tmp[index]['type'] == 'title':
                            result = result + '{"type": "title","title": ""},'
                        elif tmp[index]['type'] == 'options':
                            default_val[tmp[index]['key']
                                        ] = tmp[index]['default']
                            result = result + '{"type": "' + tmp[index]['type'] \
                                + '","title":"' + tmp[index]['title'] \
                                + '","desc":"' + tmp[index]['desc'] \
                                + '","section":"' + APP_NAME \
                                + '","key":"' + tmp[index]['key'] \
                                + '","options":' + json.dumps(tmp[index]['options']) \
                                + '},'
                        else:
                            default_val[tmp[index]['key']
                                        ] = tmp[index]['default']
                            result = result + '{"type": "' + tmp[index]['type'] \
                                + '","title":"' + tmp[index]['title'] \
                                + '","desc":"' + tmp[index]['desc'] \
                                + '","section":"' + APP_NAME \
                                + '","key":"' + tmp[index]['key'] \
                                + '"},'
                    result = result[0:-1] + "]"

                    # Update the default value and setting menu
                    settings.add_json_panel(APP_NAME, config, data=result)

    def build_config(self, config):
        # Yuanjie: the ordering of the following options MUST be the same as
        # those in settings.json!!!
        config.setdefaults('mi_general', {
            'bcheck_update': 0,
            'log_level': 'info',
            'bstartup': 0,
            'bstartup_service': 0,
            'bgps': 1,
            'start_service': 'NetLogger',
        })
        self.create_app_default_config(config)

    def create_app_default_config(self, config):
        app_list = get_plugins_list()
        for app in app_list:
            APP_NAME = app
            APP_DIR = app_list[app][0]
            setting_path = os.path.join(APP_DIR, "settings.json")
            if os.path.exists(setting_path):
                with open(setting_path, "r") as settings_json:
                    raw_data = settings_json.read()

                    # Regulate the config into the format that kivy can accept
                    tmp = eval(raw_data)

                    default_val = {}

                    for index in range(len(tmp)):
                        if tmp[index]['type'] == 'title':
                            pass
                        elif 'default' in tmp[index]:
                            default_val[tmp[index]['key']
                                        ] = tmp[index]['default']

                    # Update the default value and setting menu
                    config.setdefaults(APP_NAME, default_val)

    def build(self):

        
        # Force to initialize all configs in .mobileinsight.ini
        # This prevents missing config due to existence of older-version .mobileinsight.ini
        # Work-around: force on_config_change, which would update config.ini
        config = self.load_config()
        val = int(config.get('mi_general', 'bcheck_update'))
        config.set('mi_general', 'bcheck_update', int(not val))
        config.write()
        config.set('mi_general', 'bcheck_update', val)
        config.write()

        self.screen = MobileInsightScreen(name='MobileInsightScreen')
        self.manager = ScreenManager()
        self.manager.add_widget(self.screen)

        try:
            self.log_viewer_screen = LogViewerScreen(
                name='LogViewerScreen', screen_manager=self.manager)
            self.manager.add_widget(self.log_viewer_screen)
        except Exception as e:
            import traceback
            import crash_app
            print str(traceback.format_exc())
            self.screen.ids.log_viewer.disabled = True
            self.screen.ids.stop_plugin.disabled = True
            self.screen.ids.run_plugin.disabled = True

        self.manager.current = 'MobileInsightScreen'
        Window.borderless = False

        # return self.screen
        return self.manager

    def on_pause(self):
        # Yuanjie: The following code prevents screen freeze when screen off ->
        # screen on
        try:
            pm = current_activity.getSystemService(
                autoclass('android.content.Context').POWER_SERVICE)
            if not pm.isInteractive():
                current_activity.moveTaskToBack(True)
        except Exception as e:
            try:
                # API 20: pm.isScreenOn is depreciated
                pm = current_activity.getSystemService(
                    autoclass('android.content.Context').POWER_SERVICE)
                if not pm.isScreenOn():
                    current_activity.moveTaskToBack(True)
            except Exception as e:
                import traceback
                import crash_app
                print str(traceback.format_exc())

        # print "on_pause"
        return True  # go into Pause mode

    def on_resume(self):
        # print "on_resume"
        pass

    def check_update(self):
        """
        Check if new update is available
        """
        try:
            config = ConfigParser()
            config.read('/sdcard/.mobileinsight.ini')
            bcheck_update = config.get("mi_general", "bcheck_update")
            if bcheck_update == "1":
                import check_update
                check_update.check_update()
        except Exception as e:
            import traceback
            print str(traceback.format_exc())

    def on_start(self):
        from kivy.config import Config
        Config.set('kivy', 'exit_on_escape', 0)

        self.check_update()

    def on_stop(self):
        self.screen.stop_service()

if __name__ == "__main__":
    try:
        MobileInsightApp().run()
    except Exception as e:
        import traceback
        import crash_app
        print str(traceback.format_exc())
        crash_app.CrashApp().run()
