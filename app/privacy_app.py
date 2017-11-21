import kivy
kivy.require('1.0.9')

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.properties import *
from kivy.config import ConfigParser, Config
from kivymd.theming import ThemeManager

import httplib
import urllib
import urllib2
import subprocess
import os
import sys
import re
import datetime
import main_utils

__all__ = ["PrivacyPopup", "PrivacyApp"]

Builder.load_string('''
<PrivacyPopup>:
    cols:1
    Label:
        text: root.text
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1]
    GridLayout:
        cols: 2
        size_hint_y: None
        width: self.width
        height: '44sp'
        Button:
            text: 'Agree'
            on_release: root.dispatch('on_answer','yes')
        Button:
            text: 'Disagree'
            on_release: root.dispatch('on_answer', 'no')
''')


class PrivacyPopup(GridLayout):
    text = StringProperty()


    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(PrivacyPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class PrivacyApp(App):
    theme_cls = ThemeManager()

    def build(self):
        file = open("privacy_agreement.txt")
        privacy_agreement = file.read()
        content = PrivacyPopup(text=privacy_agreement)
        content.bind(on_answer=self._on_answer)
        self.popup = Popup(title="Privacy Notice",
                           content=content,
                           size_hint=(None, None),
                           size=(1200, 750),
                           auto_dismiss=False)
        self.popup.open()

    def _on_answer(self, instance, answer):
        if answer == "yes":
            config = ConfigParser()
            config.read('/sdcard/.mobileinsight.ini')
            config.set("mi_general","privacy",1)
            config.write()
            self.popup.dismiss()
        elif answer == "no":
            # self.popup.dismiss()
            # App.get_running_app().stop()
            App.get_running_app().stop()
    
    def on_stop(self):
        pass
