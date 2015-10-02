import kivy
kivy.require('1.0.9')

from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, StringProperty
from kivy.app import App

import sys
import traceback

Builder.load_string("""
<HelloWorldScreen>:
    cols: 1

    Label:
        text: '%s' % root.error_log
        text_size: self.size
        size_hint_y: 6
        valign: 'top'

    Button:
        text: 'Run script!'
        size_hint_y: 1
        on_release: root.my_callback()
""")

class HelloWorldScreen(GridLayout):
    error_log = StringProperty("Nico-Nico-Ni!")

    def __init__(self):
        super(HelloWorldScreen, self).__init__()

    def my_callback(self):
        no_error = True
        if no_error:
            try:
                import mobile_insight
            except:
                self.error_log = str(traceback.format_exc())
                no_error = False
        
        if no_error:
            try:
                import mobile_insight.dm_collector_c
                self.error_log = "Loaded dm_collector_c v%s" % mobile_insight.dm_collector_c.version
            except:
                self.error_log = "Failed to load dm_collector_c"
                no_error = False

        if no_error:
            try:
                execfile('/sdcard/execfile_test.py')
            except:
                self.error_log = str(traceback.format_exc())


class HelloWorldApp(App):
    def build(self):
        return HelloWorldScreen()

if __name__ == "__main__":
    HelloWorldApp().run()
