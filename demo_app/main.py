import kivy
kivy.require('1.0.9')
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty
from kivy.app import App

import sys
import traceback

Builder.load_string('''
<HelloWorldScreen>:
    cols: 1
    Label:
        text: '%s' % root.error_log
    Button:
        text: 'Click me! %d' % root.counter
        on_release: root.my_callback2()
''')

class HelloWorldScreen(GridLayout):
    counter = NumericProperty(0)
    error_log = ""
    def my_callback(self):
        print 'The button has been pushed'
        self.counter += 1

    def my_callback2(self):
        #Try execfile()
        print "Test execfile"
        try:
            execfile('/sdcard/execfile_test.py')
        except:
            f = open('/sdcard/python_log.txt','w')
            f.write(str(traceback.format_exc()))
            f.close()

    def my_callback3(self):
        try:
            import mobile_insight
        except:
            f = open('/sdcard/python_log.txt','w')
            f.write(str(traceback.format_exc()))
            f.close()

    def my_callback4(self):
        f = open("/sdcard/python_log.txt", "w")
        try:
            import mobile_insight.dm_collector_c
            print >> f, "Loaded dm_collector_c v%s" % mobile_insight.dm_collector_c.version
        except:
            print >> f, "Failed to load dm_collector_c"
        f.close()
    

class HelloWorldApp(App):
    def build(self):
        return HelloWorldScreen()

if __name__ == '__main__':

    HelloWorldApp().run()
