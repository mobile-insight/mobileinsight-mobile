import kivy

kivy.require('1.0.9')

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.properties import *
from kivy.config import ConfigParser
from .kivymd.theming import ThemeManager

__all__ = ["PrivacyPopup", "PrivacyApp", "disagree_privacy"]

Builder.load_string('''
<PrivacyPopup>:
    name: "PrivacyPopup"
    id: privacypopup
    cols:1
    sColor: [30/255.0, 100/255.0, 180/255.0, .85] # rgb colors must be percentages
    eColor: [.54, .87, .92, .85]
    color: 1,1,1,1
    Label:
        text: root.text
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1]
        markup: True
        on_ref_press:
            import webbrowser
            webbrowser.open('http://www.mobileinsight.net/privacy.html')
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '44sp'
        Button:
            text: 'I agree'
            on_release: root.dispatch('on_answer','yes')
            background_color: 0.1,0.65,0.88,1
            color: 1,1,1,1
        Button:
            text: 'I do not agree'
            on_release: root.dispatch('on_answer', 'no')
            background_color: 0.1,0.65,0.88,1
            color: 1,1,1,1
''')


# disagree_privacy = 0


class PrivacyPopup(GridLayout):
    text = StringProperty()
    theme_cls = ThemeManager()

    def __init__(self, **kwargs):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = 'Blue'
        self.register_event_type('on_answer')
        super(PrivacyPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class PrivacyApp(App):
    theme_cls = ThemeManager()

    def build(self):
        file = open("privacy_agreement.txt")
        privacy_agreement = file.read()
        privacy_agreement = privacy_agreement + '\nDo you agree to share data collected on your phone?'
        content = PrivacyPopup(text=privacy_agreement)
        content.bind(on_answer=self._on_answer)
        self.popup = Popup(title="Agreement on Data Sharing",
                           content=content,
                           size_hint=(None, None),
                           size=(1200, 2300),
                           auto_dismiss=False)
        self.popup.open()

    def _on_answer(self, instance, answer):
        if answer == "yes":
            config = ConfigParser()
            config.read('/sdcard/.mobileinsight.ini')
            config.set("mi_general", "privacy", 1)
            config.set("NetLogger", "privacy", 1)
            config.write()
            self.popup.dismiss()
        elif answer == "no":
            # global disagree_privacy
            # disagree_privacy = 1
            config = ConfigParser()
            config.read('/sdcard/.mobileinsight.ini')
            config.set("mi_general", "privacy", 1)
            config.set("NetLogger", "privacy", 0)
            config.write()
            self.popup.dismiss()
            # App.get_running_app().stop()

    def on_stop(self):
        pass
