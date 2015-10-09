'''
main-sql-android.py

This code demonstrates how to access SQLlite with python-for-android

Author: Yuanjie Li
'''

from jnius import autoclass
import kivy
kivy.require('1.0.9')
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty
from kivy.app import App

import os
import sys
import traceback

Builder.load_string('''
<HelloWorldScreen>:
    cols: 1
    Label:
        text: '%s' % root.log

    Button:
        text: 'Setup SQL' 
        on_release: root.setup_callback()

    Button:
        text: 'Query' 
        on_release: root.query_callback()
''')

class HelloWorldScreen(GridLayout):
    log = ""
    def setup_callback(self):
        try:
            activity = autoclass('org.renpy.android.PythonActivity')
            mydatabase = activity.mActivity.openOrCreateDatabase('MobileInsight.db',0,None)
            # mydatabase.execSQL("CREATE TABLE PythonHelloWorld(Username VARCHAR,Password VARCHAR);")
            mydatabase.execSQL("INSERT INTO PythonHelloWorld VALUES('hello','world');")
        except:
            f = open('/sdcard/sql_err.txt','w')
            f.write(str(traceback.format_exc()))
            f.close()
        

    def query_callback(self):
        try:
            activity = autoclass('org.renpy.android.PythonActivity')
            mydatabase = activity.mActivity.openOrCreateDatabase('MobileInsight.db',0,None)
            resultSet = mydatabase.rawQuery("Select * from PythonHelloWorld",None);
            resultSet.moveToFirst();
            f = open('/sdcard/sql_result.txt','w')
            while True:
                username = resultSet.getString(0);
                password = resultSet.getString(1);
                f.write(username + " " + password + '\n')
                if not resultSet.moveToNext():
                    break
            f.close()

        except:
            f = open('/sdcard/sql_err.txt','w')
            f.write(str(traceback.format_exc()))
            f.close()
            



class HelloWorldApp(App):
    def build(self):
        return HelloWorldScreen()

if __name__ == '__main__':

    HelloWorldApp().run()