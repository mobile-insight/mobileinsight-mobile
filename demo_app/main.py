import kivy
kivy.require('1.0.9')

from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import *

from kivy.lang import Builder
from kivy.app import App
from kivy.core.window import Window

import sys
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
""")

class HelloWorldScreen(GridLayout):
    error_log = StringProperty("Nico-Nico-Ni!")

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
                self._add_log_line("Imported mobile_insight")
            except:
                self._add_log_line(str(traceback.format_exc()))
                no_error = False
        
        if no_error:
            try:
                import mobile_insight.monitor.dm_collector.dm_collector_c as dm_collector_c
                self._add_log_line("Loaded dm_collector_c v%s" % dm_collector_c.version)
            except:
                self._add_log_line("Failed to load dm_collector_c")
                no_error = False

        if no_error:
            try:
                filename = self.ids["filename"].text
                self._add_log_line("execfile: %s" % filename)
                execfile(filename)
            except:
                self._add_log_line(str(traceback.format_exc()))


class HelloWorldApp(App):
    def build(self):
        return HelloWorldScreen()


if __name__ == "__main__":
    HelloWorldApp().run()
