import kivy

kivy.require('1.4.0')

from jnius import autoclass
from kivy.app import App
from kivy.logger import Logger
from kivy.config import ConfigParser, Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

import main_utils
from main_utils import current_activity, get_plugins_list, create_folder
import screens

Logger.info("Import Screens")

import json
import os
import time
import traceback

# sys.path.append('/vagrant/mi-dev/mobileinsight-mobile/app/kivymd')
from kivymd.date_picker import MDDatePicker
from kivymd.theming import ThemeManager
from kivymd.time_picker import MDTimePicker

# not working
# SERVICE_DIR = os.path.join(os.getcwd(), 'service')
# sys.path.append(SERVICE_DIR)
Logger.info("Import Coordinator")
from coordinator import COORDINATOR

Logger.info("Finish Import")

Builder.load_string('''
<ConfirmPopup>:
    Label:
        text: root.text
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1]
        markup: True  
    Button:
        text: 'OK'
        on_release: root.dispatch('on_answer','yes')
        background_color: 0.1,0.65,0.88,1
        color: 1,1,1,1
''')
Logger.info("Finish Builder")

# Load main UI
Window.softinput_mode = "pan"
Window.clearcolor = (1, 1, 1, 1)

Logger.info("Loading UI")


class ConfirmPopup(BoxLayout):
    text = StringProperty()

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        Logger.error("WTF")
        pass


class MobileInsightApp(App):
    Logger.info("build MI Class")
    theme_cls = ThemeManager()
    previous_date = ObjectProperty()
    title = "MobileInsight"

    index = NumericProperty(0)
    current_title = StringProperty()
    screen_names = ListProperty([])

    use_kivy_settings = False
    Logger.info("Finish build MI Class")

    def __init__(self, **kwargs):
        Logger.info("Initializing APP")
        super(MobileInsightApp, self).__init__(**kwargs)
        self.title = 'MobileInsight'
        self.screens = {}
        self.available_screens = screens.__all__
        self.home_screen = None
        self.log_viewer_screen = None

        if not create_folder():
            # MobileInsight folders unavailable. Add warnings
            Logger.error("main: SDcard is unavailable. Please check.")
        main_utils.init_libs()
        main_utils.check_security_policy()
        COORDINATOR.start()  # FIXME: DEADLOCK HERE!!!

    def __del__(self):
        Logger.error("__del__")

    # This function is added to remove remove the presplash manually
    def on_enter(self):
        # This function is called when everything is fully loaded and the app is ready
        Clock.schedule_once(self.remove_android_splash, 0.3)

    def remove_android_splash(self, *args):
        activity = PythonActivity.mActivity
        activity.removeLoadingScreen()


    def __popup_dismiss(self, instance, answer):
        self.popup.dismiss()
        self.stop()
        return True

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
        config.read('/sdcard/.mobileinsight.ini')
        config.setdefaults('mi_general', {
            'bcheck_update': 0,
            'log_level': 'info',
            'bstartup': 0,
            'bstartup_service': 0,
            'bgps': 1,
            'start_service': 'KPIAnalyzer',
            'privacy': 1,
        })
        self.create_app_default_config(config)
        config.write()

    def create_app_default_config(self, config):
        app_list = get_plugins_list()
        for app in app_list:
            APP_NAME = app
            APP_DIR = app_list[app][0]
            setting_path = os.path.join(APP_DIR, "settings.json")
            if os.path.exists(setting_path):
                Logger.info("default path:"+setting_path)
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
        # Logger.info("Building APP")
        # config = self.load_config()
        config = self.config
        # val = int(config.get('mi_general', 'bcheck_update'))
        # config.set('mi_general', 'bcheck_update', int(not val))
        config.set('mi_general', 'bcheck_update', 0)
        config.write()

        Window.borderless = False

        self.screens = {}
        self.available_screens = screens.__all__
        self.screen_names = self.available_screens
        for i in range(len(self.available_screens)):
            self.screens[i] = getattr(screens, self.available_screens[i])()
        self.home_screen = self.screens[0]
        COORDINATOR.setup_analyzers()
        COORDINATOR.send_control('START')
        self.root.ids.scr_mngr.switch_to(self.screens[0])

    def go_screen(self, idx):
        if self.index == idx:
            return
        self.index = idx
        self.root.ids.scr_mngr.switch_to(self.load_screen(idx), direction='left')

    def load_screen(self, index):
        return self.screens[index]

    def get_time_picker_data(self, instance, time):
        self.root.ids.time_picker_label.text = str(time)
        self.previous_time = time

    def show_example_time_picker(self):
        self.time_dialog = MDTimePicker()
        self.time_dialog.bind(time=self.get_time_picker_data)
        if self.root.ids.time_picker_use_previous_time.active:
            try:
                self.time_dialog.set_time(self.previous_time)
            except AttributeError:
                pass
        self.time_dialog.open()

    def set_previous_date(self, date_obj):
        self.previous_date = date_obj
        self.root.ids.date_picker_label.text = str(date_obj)

    def show_example_date_picker(self):
        if self.root.ids.date_picker_use_previous_date.active:
            pd = self.previous_date
            try:
                MDDatePicker(self.set_previous_date,
                             pd.year, pd.month, pd.day).open()
            except AttributeError:
                MDDatePicker(self.set_previous_date).open()
        else:
            MDDatePicker(self.set_previous_date).open()

    def set_error_message(self, *args):
        if len(self.root.ids.text_field_error.text) == 2:
            self.root.ids.text_field_error.error = True
        else:
            self.root.ids.text_field_error.error = False

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
                Logger.exception(traceback.format_exc())

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
            config = self.config
            # config = ConfigParser()
            # config.read('/sdcard/.mobileinsight.ini')
            bcheck_update = config.get("mi_general", "bcheck_update")
            if bcheck_update == "1":
                from . import check_update
                check_update.check_update()
        except Exception as e:
            Logger.exception(traceback.format_exc())

    def privacy_check(self):
        """
        Check if new update is available
        """
        try:
            # config = ConfigParser()
            # config.read('/sdcard/.mobileinsight.ini')
            config = self.config
            privacy_agreed = int(config.get("mi_general", "privacy"))
            if privacy_agreed == 0:
                import privacy_app
                privacy_app.PrivacyApp().run()
                # if privacy_app.disagree_privacy:
                #     self.stop()
        except Exception as e:
            Logger.exception(traceback.format_exc())

    def on_start(self):
        # android.stop_service() # Kill zombine service from previous app instances

        Config.set('kivy', 'exit_on_escape', 0)

        if not main_utils.is_rooted():
            err_str = "MobileInsight requires root privilege. Please root your device for correct functioning."
            Logger.error(err_str)
            self.home_screen.log_error(err_str)
        elif not main_utils.check_diag_mode():
            err_str = "The diagnostic mode is disabled. Please check your phone settings."
            Logger.error(err_str)
            self.home_screen.log_error(err_str)
            # content = ConfirmPopup(text=err_str)
            # content.bind(on_answer=self.__popup_dismiss)
            # self.popup = Popup(title='Diagnostic mode is not available',
            #             content=content,
            #             size_hint=(None, None), 
            #             size=(1200, 400),
            #             auto_dismiss=False)
            # self.popup.open()
        else:
            self.privacy_check()
            self.check_update()

    def on_stop(self):
        Logger.error("on_stop")
        COORDINATOR.stop()


time.sleep(0.5)

Logger.info("Begin Main")

if __name__ == "__main__":
    try:
        MobileInsightApp().run()
        Logger.error("MobileInsight Error. Existing")
    except Exception as e:
        from . import crash_app

        Logger.exception(traceback.format_exc())
        crash_app.CrashApp().run()
    finally:
        pass
