import kivy
kivy.require('1.0.9')

from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import *

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import platform
from kivy.config import ConfigParser

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

#Load main UI
Window.softinput_mode = "pan"
Window.clearcolor = (1, 1, 1, 1)
Builder.load_file('main_ui.kv')
current_activity = cast("android.app.Activity", autoclass("org.renpy.android.PythonActivity").mActivity)

LOGO_STRING = "MobileInsight "+main_utils.get_cur_version()+"\nUCLA WiNG Group & OSU MSSN Lab"




def create_folder():

    mobile_insight_path = main_utils.get_mobile_insight_path()

    if not mobile_insight_path:
        return False

    cmd = "mkdir "+mobile_insight_path+"; "
    cmd = cmd + "mkdir " + main_utils.get_mobile_insight_log_path() +"; "
    cmd = cmd + "mkdir " + main_utils.get_mobile_insight_analysis_path() +"; "
    cmd = cmd + "mkdir " + main_utils.get_mobile_insight_cfg_path()+"; "
    cmd = cmd + "mkdir " + main_utils.get_mobile_insight_db_path()+"; "
    cmd = cmd + "mkdir " + main_utils.get_mobile_insight_plugin_path()+"; "
    cmd = cmd + "mkdir " + main_utils.get_mobile_insight_log_decoded_path()+"; "
    cmd = cmd + "mkdir " + main_utils.get_mobile_insight_log_uploaded_path()+"; "
    cmd = cmd + "mkdir " + main_utils.get_mobile_insight_crash_log_path()+"; "
    cmd = cmd + "chmod -R 755 "+mobile_insight_path+"; "
    main_utils.run_shell_cmd(cmd)

    return True

def get_app_list():

    '''
    Load plugin lists, including both buil-in and 3rd-party plugins
    '''

    ret = {} # app_name->(path,with_UI)

    APP_DIR = os.path.join(str(current_activity.getFilesDir().getAbsolutePath()), "app")
    l = os.listdir(APP_DIR)
    for f in l:
        if os.path.exists(os.path.join(APP_DIR, f, "main.mi2app")):
            # ret.append(f)
            ret[f] = (os.path.join(APP_DIR, f), False)

    # Yuanjie: support alternative path for users to customize their own app
    APP_DIR = main_utils.get_mobile_insight_plugin_path()

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
        create_folder()

    return ret
       
def check_update():
    try:
        config = ConfigParser()
        config.read('/sdcard/.mobileinsight.ini')
        bcheck_update = config.get("mi_general", "bcheck_update")
        if bcheck_update=="1":
            import check_update
            check_update.check_update()
    except Exception, e:
        import traceback,crash_app
        print str(traceback.format_exc())

class MobileInsightScreen(GridLayout):
    error_log = StringProperty(LOGO_STRING)
    default_app_name = StringProperty("")
    collecting = BooleanProperty(False)
    service = None
    analyzer = None
    terminal_thread = None
    terminal_stop = None

    def __init__(self):
        super(MobileInsightScreen, self).__init__()

        self.__init_libs()
        self.__check_security_policy()
        
        if not create_folder():
            # MobileInsight folders unavailable. Add warnings
            self.error_log.add_log_line("WARINING: SDcard is unavailable. Please check.")

        self.app_list = get_app_list()
        # self.app_list.sort()

        if not self.__check_diag_mode():
            self.error_log.add_log_line("WARINING: the diagnostic mode is disabled. Please check your phone settings.")

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


        # If default service exists, launch it
        try:
            config = ConfigParser()
            config.read('/sdcard/.mobileinsight.ini')
            default_app_name = config.get("mi_general", "start_service")
            launch_service = config.get("mi_general", "bstartup_service")
            if default_app_name and launch_service=="1":
                self.start_service(default_app_name)
        except Exception, e:
            pass

    def __check_security_policy(self):
        """
        Update SELinux policy.
        For Nexus 6/6P, the SELinux policy may forbids the log collection.
        """
        main_utils.run_shell_cmd("setenforce 0")
        main_utils.run_shell_cmd("supolicy --live \"allow init diag_device chr_file {getattr write ioctl}\"")
        main_utils.run_shell_cmd("supolicy --live \"allow init init process execmem\"")
        main_utils.run_shell_cmd("supolicy --live \"allow init properties_device file execute\"")
        main_utils.run_shell_cmd("supolicy --live \"allow atfwd diag_device chr_file {read write open ioctl}\"")
        main_utils.run_shell_cmd("supolicy --live \"allow system_server diag_device chr_file {read write}\"")
        main_utils.run_shell_cmd("supolicy --live \"allow untrusted_app app_data_file file {rename}\"")
        main_utils.run_shell_cmd("supolicy --live \"allow init app_data_file fifo_file {write, open}\"")
        main_utils.run_shell_cmd("supolicy --live \"allow init app_data_file fifo_file {write, open}\"")


    def __check_diag_mode(self):
        """
        Check if diagnostic mode is enabled.
        """

        cmd = " test -e /dev/diag"
        res = main_utils.run_shell_cmd(cmd, True)
        if res:
            return False
        else:
            main_utils.run_shell_cmd("chmod 755 /dev/diag")
            return True


    def __init_libs(self):
        """
        Initialize libs required by MobileInsight
        """

        libs_path = os.path.join(main_utils.get_files_dir(), "data")

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
            main_utils.run_shell_cmd(cmd)


    def add_log_line(self, s):
        self.error_log += "\n"
        self.error_log += s

    def show_log(self):

        # log_name = os.path.join(main_utils.get_mobile_insight_path(),"log.txt")


        while not self.terminal_stop.is_set() \
        and not os.path.exists(self.log_name):
            continue

        log_file = open(self.log_name,'r')

        while True:
            if self.terminal_stop.is_set():
                # log_file.close()
                # return
                continue
            try:
                where = log_file.tell()
                line = log_file.readline()
                if not line:
                    log_file.seek(where)
                else:
                    # # Show MAX_LINE lines at most
                    # # TODO: make the code more efficient
                    MAX_LINE = 10
                    tmp = self.error_log.split('\n')
                    tmp.append(line)
                    if len(tmp)>MAX_LINE:
                        self.error_log = '\n'.join(tmp[-MAX_LINE:])
                    else:
                        self.error_log = '\n'.join(tmp)

                    # self.add_log_line(line)
            except Exception, e:
                continue


    def run_script_callback(self):
        no_error = True

        if no_error:
            try:
                filename = self.ids["filename"].text
                self.add_log_line("")
                self.add_log_line("execfile: %s" % filename)
                namespace = { "app_log": "" }
                execfile(filename, namespace)
                # Load the "app_log" variable from namespace and print it out
                self.add_log_line(namespace["app_log"])
            except:
                print str(traceback.format_exc())
                self.add_log_line(str(traceback.format_exc()))
                no_error = False

    def on_checkbox_app_active(self, obj):
        for cb in self.ids.checkbox_app_layout.children:
            if cb.active:
                self.ids.checkbox_app.selected = cb.text

        # Yuanjie: try to load readme.txt
        if self.service:
            return True

        app_path = self.app_list[self.ids.checkbox_app.selected][0]
        if os.path.exists(os.path.join(app_path, "readme.txt")):
            with open(os.path.join(app_path, "readme.txt"), 'r') as ff:
                self.error_log = self.ids.checkbox_app.selected + ": " + ff.read()
        else:
            self.error_log = self.ids.checkbox_app.selected + ": no descriptions."

        return True


    def stop_collection(self):
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
            main_utils.run_shell_cmd(cmd2)


    def start_service(self, app_name):
        if platform == "android" and app_name in self.app_list:
            if self.service:
                # stop the running service
                self.stop_service() 

            # Show logs on screen

            # Clean up old logs
            self.log_name = os.path.join(main_utils.get_mobile_insight_analysis_path(),app_name+"_log.txt")
            if os.path.exists(self.log_name):
                os.remove(self.log_name)

            self.terminal_stop = threading.Event()
            self.terminal_thread = threading.Thread(target=self.show_log)
            self.terminal_thread.start()

            
            from android import AndroidService
            self.error_log = "Running " + app_name + "..."
            self.service = AndroidService("MobileInsight is running...", app_name)
            self.service.start(app_name+":"+self.app_list[app_name][0])   # app name
            self.default_app_name = app_name

        else:
            self.error_log = "Error: " + app_name + "cannot be launched!"

    def stop_service(self):
        if self.service:
            self.service.stop()
            self.service = None
            if self.terminal_stop:
                self.terminal_stop.set()
            self.error_log = LOGO_STRING

            self.stop_collection()  # close ongoing collections
            
            # Haotian: save orphan log
            dated_files = []
            self.__logdir = main_utils.get_mobile_insight_log_path()
            self.__phone_info = main_utils.get_phone_info()
            mi2log_folder = os.path.join(main_utils.get_cache_dir(), "mi2log")
            for subdir, dirs, files in os.walk(mi2log_folder):
                for f in files:
                    fn = os.path.join(subdir, f)
                    dated_files.append((os.path.getmtime(fn), fn))
            dated_files.sort()
            dated_files.reverse()
            if len(dated_files)>0:
                self.__original_filename = dated_files[0][1]
                print "The last orphan log file: " + str(self.__original_filename)
                chmodcmd = "chmod 644 " + self.__original_filename
                p = subprocess.Popen("su ", executable = main_utils.ANDROID_SHELL, shell = True, \
                                            stdin = subprocess.PIPE, stdout = subprocess.PIPE)
                p.communicate(chmodcmd + '\n')
                p.wait()
                self._save_log()

    def _save_log(self):
        orig_basename  = os.path.basename(self.__original_filename)
        orig_dirname   = os.path.dirname(self.__original_filename)
        self.__log_timestamp     = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        milog_basename = "diag_log_%s_%s_%s.mi2log" % (self.__log_timestamp, self.__phone_info, main_utils.get_operator_info())
        milog_absname  = os.path.join(self.__logdir, milog_basename)
        shutil.copyfile(self.__original_filename, milog_absname)
        chmodcmd = "rm -f " + self.__original_filename
        p = subprocess.Popen("su ", executable = main_utils.ANDROID_SHELL, shell = True, \
                                    stdin = subprocess.PIPE, stdout = subprocess.PIPE)
        p.communicate(chmodcmd + '\n')
        p.wait()

    def about(self):
        about_text = ('MobileInsight '+main_utils.get_cur_version()+' \n' 
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
            settings.add_json_panel('General', self.config, data=settings_json.read())

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
        config.setdefaults('mi_general', {
            'bcheck_update': 1,
            'bstartup': 0,
            'bstartup_service': 0,
            'start_service': 'NetLoggerInternal',
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
        self.manager = ScreenManager()
        Window.borderless = False
        return self.screen

    def on_pause(self):
        # Yuanjie: The following code prevents screen freeze when screen off -> screen on
        try:
            pm = current_activity.getSystemService(autoclass('android.content.Context').POWER_SERVICE);
            if not pm.isInteractive():
                current_activity.moveTaskToBack(True)
        except Exception, e:
            try:
                # API 20: pm.isScreenOn is depreciated
                pm = current_activity.getSystemService(autoclass('android.content.Context').POWER_SERVICE);
                if not pm.isScreenOn():
                    current_activity.moveTaskToBack(True)
            except Exception, e:
                import traceback,crash_app
                print str(traceback.format_exc())
        return True  # go into Pause mode

    def on_resume(self):
        pass

    def on_start(self):
        from kivy.config import Config
        Config.set('kivy', 'exit_on_escape', 0)

        check_update()

    def on_stop(self):
        pass
        # self.screen.stop_service()

if __name__ == "__main__":
    try:
        MobileInsightApp().run()
    except Exception, e:
        import traceback,crash_app
        print str(traceback.format_exc())
        crash_app.CrashApp().run()

