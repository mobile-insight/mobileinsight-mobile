import kivy

kivy.require('1.4.0')

import os
import threading
import time
import datetime
from android import AndroidService
from android.broadcast import BroadcastReceiver
from collections import deque
from jnius import autoclass
from kivy.utils import platform
from kivy.logger import Logger
from kivy.core.text import Label as CoreLabel
from kivy.config import ConfigParser
from kivy.properties import StringProperty, BooleanProperty
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from main import get_plugins_list
import main_utils
from main_utils import current_activity
from . import MobileInsightScreenBase
import traceback

Builder.load_file('screens/home.kv')

LOGO_STRING = "MobileInsight " + main_utils.get_cur_version() + \
              "\nCopyright (c) 2015-2017 MobileInsight Team"


class HomeScreen(MobileInsightScreenBase):
    error_log = StringProperty(LOGO_STRING)
    default_app_name = StringProperty("")
    collecting = BooleanProperty(False)
    service = None
    analyzer = None
    terminal_thread = None
    terminal_stop = None
    MAX_LINE = 30
    logs = deque([], MAX_LINE)
    plugins = []
    selectedPlugin = ""
    app_list = get_plugins_list()
    myLayout = GridLayout(cols=2, spacing=5,
                          orientation="vertical",
                          size_hint_y=None,
                          height=(len(app_list) / 2 + len(app_list) % 2) * Window.height / 4)
    popupScroll = ScrollView(size_hint_y=None, size=(Window.width, Window.height * .9))
    popupScroll.add_widget(myLayout)
    popup = Popup(content=popupScroll, title="Choose a plugin")

    def __init__(self, **kw):
        """
        Initialization function. We will do the following task (in order):
        __[x] means already done in App__
            1. [x] Check if the device is rooted
            2. [x] Initialize necessary libs required by MobileInsight (e.g., libwireshark)
            3. [x] Check if Android's security policy allows MobileInsight to access diagnostic mode.
            This is mainly caused by SELinux
            4. [x] Create necessary folders on SDcard (e.g., /sdcard/mobileinsight/, /sdcard/mobileinsight/log/)
            5. Load built-in and 3rd-party plugins (located in /sdcard/mobileinsight/plugins/)
            6. [x] Check if the diagnostic mode is enabled
            7. Load configurations from the setting panel (configs stored in /sdcard/.mobileinsight.ini)
        """

        super(HomeScreen, self).__init__(**kw)

        self.log_viewer = None

        # if not main_utils.is_rooted():
        #     # self.ids.log_viewer.disabled = False
        #     # self.ids.run_plugin.disabled = False
        #     self.log_error(
        #         "MobileInsight requires root privilege. Please root your device for correct functioning.")

        # self.__init_libs()
        # self.__check_security_policy()

        # if not create_folder():
        #     # MobileInsight folders unavailable. Add warnings
        #     self.log_error("SDcard is unavailable. Please check.")
        #     self.ids.log_viewer.disabled = True
        #     self.ids.stop_plugin.disabled = True
        #     self.ids.run_plugin.disabled = True

        self.plugins_list = get_plugins_list()
        # self.plugins_list.sort()

        # if not self.__check_diag_mode():
        #     self.log_error(
        #         "The diagnostic mode is disabled. Please check your phone settings.")

        # clean up ongoing log collections
        # self.stop_collection()

        self.terminal_stop = None
        self.terminal_thread = None
        bootup = True

        # used to shorten long widget names in popup menu
        shortenLabel = CoreLabel(markup=True, text_size=(Window.width / 2.5, None), shorten_from="right", font_size=70)
        # Making and adding widgets to popup menu
        for name in self.plugins_list:
            widget = Button(id=name, markup=True, halign="left", valign="top", on_release=self.callback,
                            background_normal="", background_color=self.ids.run_plugin.background_color)
            widget.text_size = (Window.width / 2.25, Window.height / 4)
            self.myLayout.add_widget(widget)

            app_path = self.plugins_list[name][0]
            if os.path.exists(os.path.join(app_path, "readme.txt")):
                with open(os.path.join(app_path, "readme.txt"), 'r') as ff:
                    my_description = ff.read()
            else:
                my_description = "no description."
            # shortening long widget names and making font size
            shortenedName = shortenLabel.shorten(name)
            font_size = "60"
            if Window.width < 1450:
                font_size = "45"
            widget.text = "[color=fffafa][size=70]" + shortenedName + "[/size][size=" + font_size + "]\n" + my_description + "[/size][/color]"

            if bootup:
                self.selectedPlugin = name
                # self.ids.selectButton.text = "Select Plugin"
                self.ids.run_plugin.text = "Run Plugin: " + self.selectedPlugin
                bootup = False

        # register Broadcast Receivers.
        self.registerBroadcastReceivers()

        # If default service exists, launch it
        try:
            config = ConfigParser()
            config.read('/sdcard/.mobileinsight.ini')
            default_app_name = config.get("mi_general", "start_service")
            launch_service = config.get("mi_general", "bstartup_service")
            if default_app_name and launch_service == "1":
                self.start_service(default_app_name)
                self.ids.run_plugin.text = "Stop Plugin: " + default_app_name
        except Exception as e:
            Logger.warning(traceback.format_exc())

    def registerBroadcastReceivers(self):
        self.brStopAck = BroadcastReceiver(self.on_broadcastStopServiceAck,
                                           actions=['MobileInsight.Plugin.StopServiceAck'])
        self.brStopAck.start()

    def set_plugin(self, plugin_name):
        print("set_plugin")
        self.selectedPlugin = plugin_name
        if not self.service:
            self.ids.run_plugin.text = "Run Plugin: " + self.selectedPlugin

    # @staticmethod
    # def set_plugin(plugin_name):
    #     selectedPlugin = plugin_name
    #     if not HomeScreen.service:
    #         HomeScreen.ids.run_plugin.text  = "Run Plugin: "+selectedPlugin

    # Setting the text for the Select Plugin Menu button
    def callback(self, obj):
        self.selectedPlugin = obj.id
        # self.ids.selectButton.text = "Select Button: " + obj.text[(obj.text.find("]", obj.text.find("]")+1)+1):obj.text.find("[", obj.text.find("[", obj.text.find("[")+1)+1)]
        # self.ids.selectButton.text = "Select Plugin"
        if not self.service:
            self.ids.run_plugin.text = "Run Plugin: " + self.selectedPlugin
        self.popup.dismiss()

    def log_info(self, msg):
        Logger.info(msg)
        self.append_log("[b][color=00ff00][INFO][/color][/b]: " + msg)

    def log_warning(self, msg):
        Logger.warning(msg)
        self.append_log("[b][color=00ffff][WARNING][/color][/b]: " + msg)

    def log_error(self, msg):
        Logger.error(msg)
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

    # def __check_security_policy(self):
    #     """
    #     Update SELinux policy.
    #     For Nexus 6/6P, the SELinux policy may forbids the log collection.
    #     """

    #     cmd = "setenforce 0; "

    #     cmd = cmd + "supolicy --live \"allow init logd dir getattr\";"

    #     # # Depreciated supolicies. Still keep them for backup purpose
    #     cmd = cmd + "supolicy --live \"allow init init process execmem\";"
    #     cmd = cmd + \
    #         "supolicy --live \"allow atfwd diag_device chr_file {read write open ioctl}\";"
    #     cmd = cmd + "supolicy --live \"allow init properties_device file execute\";"
    #     cmd = cmd + \
    #         "supolicy --live \"allow system_server diag_device chr_file {read write}\";"

    #     # # Suspicious supolicies: MI works without them, but it seems that they SHOULD be enabled...

    #     # # mi2log permission denied (logcat | grep denied), but no impact on log collection/analysis
    #     cmd = cmd + \
    #         "supolicy --live \"allow untrusted_app app_data_file file {rename}\";"

    #     # # Suspicious: why still works after disabling this command? Won't FIFO fail?
    #     cmd = cmd + \
    #         "supolicy --live \"allow init app_data_file fifo_file {write open getattr}\";"
    #     cmd = cmd + \
    #         "supolicy --live \"allow init diag_device chr_file {getattr write ioctl}\"; "

    #     # Nexus 6 only
    #     cmd = cmd + \
    #         "supolicy --live \"allow untrusted_app diag_device chr_file {write open getattr}\";"
    #     cmd = cmd + \
    #         "supolicy --live \"allow system_server diag_device chr_file {read write}\";"
    #     cmd = cmd + \
    #         "supolicy --live \"allow netmgrd diag_device chr_file {read write}\";"
    #     cmd = cmd + \
    #         "supolicy --live \"allow rild diag_device chr_file {read write}\";"
    #     cmd = cmd + \
    #         "supolicy --live \"allow rild debuggerd app_data_file {read open getattr}\";"

    #     cmd = cmd + \
    #         "supolicy --live \"allow wcnss_service mnt_user_file dir {search}\";"

    #     cmd = cmd + \
    #         "supolicy --live \"allow wcnss_service fuse dir {read open search}\";"

    #     cmd = cmd + \
    #         "supolicy --live \"allow wcnss_service mnt_user_file lnk_file {read}\";"

    #     cmd = cmd + \
    #         "supolicy --live \"allow wcnss_service fuse file {read append getattr}\";"

    #     main_utils.run_shell_cmd(cmd)

    # def __check_diag_mode(self):
    #     """
    #     Check if diagnostic mode is enabled.
    #     Note that this function is chipset-specific: Qualcomm and MTK have different detection approaches
    #     """
    #     chipset_type = main_utils.get_chipset_type()
    #     if chipset_type == main_utils.ChipsetType.QUALCOMM:
    #         diag_port = "/dev/diag"
    #         if not os.path.exists(diag_port):
    #             return False
    #         else:
    #             main_utils.run_shell_cmd("chmod 777 /dev/diag")
    #             return True
    #     elif chipset_type == main_utils.ChipsetType.MTK:
    #         cmd = "ps | grep emdlogger1"
    #         res = main_utils.run_shell_cmd(cmd)
    #         if not res:
    #             return False
    #         else:
    #             return True

    # def __init_libs(self):
    #     """
    #     Initialize libs required by MobileInsight.
    #     It creates sym links to libs, and chmod of critical execs
    #     """

    #     libs_path = os.path.join(main_utils.get_files_dir(), "data")
    #     cmd = ""

    #     libs_mapping = {
    #         "libwireshark.so": [
    #             "libwireshark.so.6", "libwireshark.so.6.0.1"], "libwiretap.so": [
    #             "libwiretap.so.5", "libwiretap.so.5.0.1"], "libwsutil.so": [
    #             "libwsutil.so.6", "libwsutil.so.6.0.0"]}
    #     for lib in libs_mapping:
    #         for sym_lib in libs_mapping[lib]:
    #             # if not os.path.isfile(os.path.join(libs_path,sym_lib)):
    #             if True:
    #                 # TODO: chown to restore ownership for the symlinks
    #                 cmd = cmd + " ln -s " + \
    #                     os.path.join(libs_path, lib) + " " + os.path.join(libs_path, sym_lib) + "; "

    #     exes = ["diag_revealer",
    #             "diag_revealer_mtk",
    #             "android_pie_ws_dissector",
    #             "android_ws_dissector"]
    #     for exe in exes:
    #         cmd = cmd + " chmod 755 " + os.path.join(libs_path, exe) + "; "

    #     cmd = cmd + "chmod -R 755 " + libs_path
    #     main_utils.run_shell_cmd(cmd)

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
                Logger.exception(traceback.format_exc())
                continue

    def run_script_callback(self):
        no_error = True

        if no_error:
            try:
                filename = self.ids["filename"].text
                self.append_log("")
                self.append_log("execfile: %s" % filename)
                namespace = {"app_log": ""}
                exec(compile(open(filename, "rb").read(), filename, 'exec'), namespace)
                # Load the "app_log" variable from namespace and print it out
                self.append_log(namespace["app_log"])
            except BaseException:
                Logger.exception(traceback.format_exc())
                self.append_log(str(traceback.format_exc()))
                no_error = False

    def stop_collection(self):
        res = main_utils.run_shell_cmd("ps").split('\n')
        for item in res:
            if item.find('diag_revealer') != -1:
                pid = item.split()[1]
                cmd = "kill " + pid
                main_utils.run_shell_cmd(cmd)

    # def stop_collection(self):
    #     self.collecting = False

    #     # Find diag_revealer process
    #     # FIXME: No longer work for 7.0: os.listdir() only returns current
    #     # processstop_collection
    #     diag_procs = []
    #     pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
    #     print "stop_collection", str(pids)
    #     for pid in pids:
    #         try:
    #             cmdline = open(
    #                 os.path.join(
    #                     "/proc",
    #                     pid,
    #                     "cmdline"),
    #                 "rb").read()
    #             # if cmdline.startswith("diag_mdlog") or
    #             # cmdline.startswith("diag_revealer"):
    #             if cmdline.find("diag_revealer") != - \
    #                     1 or cmdline.find("diag_mdlog") != -1:
    #                 diag_procs.append(int(pid))
    #         except IOError:     # proc has been terminated
    #             continue
    #     if len(diag_procs) > 0:
    #         cmd2 = "kill " + " ".join([str(pid) for pid in diag_procs])
    #         main_utils.run_shell_cmd(cmd2)

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
                app_name + ":" + self.plugins_list[app_name][0])  # app name
            self.default_app_name = app_name

            # TODO: support collecting TCPDUMP trace
            # currentTime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            # tcpdumpcmd = "su -c tcpdump -i rmnet_data0 -w " \
            #         + main_utils.get_mobileinsight_log_path() \
            #         + "/tcpdump_" + str(currentTime) + ".pcap\n"
            # main_utils.run_shell_cmd(tcpdumpcmd)

        else:
            self.error_log = "Error: " + app_name + "cannot be launched!"

    def on_broadcastStopServiceAck(self, context, intent):
        self.log_info("Received MobileInsight.Plugin.StopServiceAck from plugin")
        self.pluginAck = True

    def stop_service(self):
        # Register listener for 'MobileInsight.Plugin.StopServiceAck' intent
        # from plugin
        # self.log_info("Ready to stop current plugin ...")
        self.pluginAck = False

        # Using broadcast to send 'MobileInsight.Main.StopService' intent to
        # plugin
        IntentClass = autoclass("android.content.Intent")
        intent = IntentClass()
        action = 'MobileInsight.Main.StopService'
        intent.setAction(action)
        try:
            current_activity.sendBroadcast(intent)
        except Exception as e:
            self.log_error(traceback.format_exc())

        if self.service:
            start_time = datetime.datetime.utcnow()
            current_time = datetime.datetime.utcnow()
            while (not self.pluginAck and (current_time - start_time).total_seconds() < 5):
                current_time = datetime.datetime.utcnow()
                pass
            self.service.stop()
            self.service = None
            if self.terminal_stop:
                self.terminal_stop.set()
            # self.error_log = LOGO_STRING
            self.log_info(
                "Plugin stopped. Detailed analytic results are saved in " +
                self.log_name)

            self.stop_collection()  # close ongoing collections (diag_revealer)

            # killall tcpdump
            # tcpdumpcmd = "su -c killall tcpdump\n"
            # main_utils.run_shell_cmd(tcpdumpcmd)

    def on_click_plugin(self, app_name):
        if self.service:
            self.stop_service()
            self.ids.run_plugin.text = "Run Plugin: " + app_name
        else:
            self.start_service(app_name)
            self.ids.run_plugin.text = "Stop Plugin: " + app_name

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

    def on_enter(self):
        # main_utils.stop_service()
        pass

    def on_leave(self):
        self.stop_service()

    def configure_coordinator(self):
        pass
