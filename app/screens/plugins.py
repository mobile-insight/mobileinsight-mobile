import kivy

kivy.require('1.4.0')

import os
from android.broadcast import BroadcastReceiver
from collections import deque
from kivy.logger import Logger
from kivy.core.text import Label as CoreLabel
from kivy.properties import StringProperty, BooleanProperty
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
# from main import get_plugins_list
import main_utils
from main_utils import get_plugins_list
from . import MobileInsightScreenBase

Builder.load_file('screens/plugins.kv')

LOGO_STRING = "MobileInsight " + main_utils.get_cur_version() + \
              "\nCopyright (c) 2015-2017 MobileInsight Team"


class PluginsScreen(MobileInsightScreenBase):
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

        super(PluginsScreen, self).__init__(**kw)

        self.log_viewer = None
        self.app_list = get_plugins_list()
        self.myLayout = GridLayout(cols=2, spacing=5,
                              # orientation="vertical",
                              size_hint_y=None,
                              height=(len(self.app_list) / 2 + len(self.app_list) % 2) * Window.height / 4)
        # myLayout = GridLayout()
        self.popupScroll = ScrollView(size_hint_y=None, size=(Window.width, Window.height * .9))
        self.popupScroll.add_widget(self.myLayout)
        self.popup = Popup(content=self.popupScroll, title="Choose a plugin")

        self.plugins_list = get_plugins_list()

        self.terminal_stop = None
        self.terminal_thread = None
        bootup = True

        # used to shorten long widget names in popup menu
        shortenLabel = CoreLabel(markup=True, text_size=(Window.width / 2.5, None), shorten_from="right", font_size=70)
        # Making and adding widgets to popup menu
        for name in self.plugins_list:
            widget = Button(id=name, markup=True, halign="left", valign="top", on_release=self.callback,
                            background_normal="", background_color=self.ids.selectButton.background_color)
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
                self.ids.selectButton.text = "Select Plugin"
                bootup = False

        # register Broadcast Receivers.
        self.registerBroadcastReceivers()

    def registerBroadcastReceivers(self):
        self.brStopAck = BroadcastReceiver(self.on_broadcastStopServiceAck,
                                           actions=['MobileInsight.Plugin.StopServiceAck'])
        self.brStopAck.start()

    # Setting the text for the Select Plugin Menu button
    def callback(self, obj):
        self.selectedPlugin = obj.id
        self.log_info("screens" + str(self.manager.screens))
        if self.manager.has_screen('HomeScreen'):
            self.manager.get_screen('HomeScreen').set_plugin(self.selectedPlugin)
            # HomeScreen.set_plugin(self.selectedPlugin)
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

    def popUpMenu(self):
        self.popup.open()

    def on_broadcastStopServiceAck(self, context, intent):
        self.log_info("Received MobileInsight.Plugin.StopServiceAck from plugin")
        self.pluginAck = True

    def on_enter(self):
        pass

    def on_leave(self):
        pass

    def configure_coordinator(self):
        pass
