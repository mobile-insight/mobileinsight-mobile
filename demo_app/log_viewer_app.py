import kivy
kivy.require('1.4.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.core.window import Window

from mobile_insight.analyzer import LogAnalyzer
from mobile_insight.monitor.dm_collector.dm_endec.dm_log_packet import DMLogPacket

from datetime import datetime, timedelta
from threading import Thread

import os
import sys
import xml.dom.minidom

#############################

Builder.load_string("""
<Window>
	grid: grid
	Button:
		id: open
		text: 'Open'
		size: root.width*0.2425, root.height*0.05
		pos: 0, root.height*0.95
		on_release: root.onOpen()
	Button:
		text: 'Filter'
		size: root.width*0.2425, root.height*0.05
		pos: root.width*0.2525, root.height*0.95
		on_release: root.onFilter()
	Button:
		text: 'Search'
		size: root.width*0.2425, root.height*0.05
		pos: root.width*0.505, root.height*0.95
		on_release: root.onSearch()
	Button:
		text: 'Reset'
		size: root.width*0.2425, root.height*0.05
		pos: root.width*0.7575, root.height*0.95
		on_release: root.onReset()
	ScrollView:
		size: root.width, root.height*19/20
		x: 0
		y: 0
		GridLayout:
			id: grid
			cols: 2
			row_force_default: True
			row_default_height: root.height/20
			size_hint_y: None
<Open_Popup>:
	BoxLayout:
		size: root.size
		pos: root.pos
		orientation: "vertical"
		FileChooserListView:	
			id: filechooser
			filters: ['/*.mi2log']
			path: '/sdcard/mobile_insight/log'
			on_selection: root.load(filechooser.path, filechooser.selection, *args)
			minimum_height: filechooser.setter('height')
""")

############################# Used for filechooser


class Open_Popup(FloatLayout):
	load = ObjectProperty(None)
	cancel = ObjectProperty(None)


#############################


class Window(Widget):
	loaded = ObjectProperty(None)
	loadfile = ObjectProperty(None)
	ok = ObjectProperty(None)
	cancel = ObjectProperty(None)


	def __init__(self):
		super(Window, self).__init__()
		self._log_analyzer = LogAnalyzer(self.OnReadComplete)
		self.selectedTypes = None


	def dismiss_open_popup(self):
		self.open_popup.dismiss()


	def dismiss_filter_popup(self, *args):
		self.filter_popup.dismiss()


	def dismiss_search_popup(self, *args):
		self.search_popup.dismiss()


############################# Open
#	Pick a .mi2log file that you would like to load.
# Logs are organized by their Type ID.
# Click the row to see the whole log


	def onOpen(self):
		self.open_popup = Popup(title = 'Load file', content = Open_Popup(load=self.load, cancel = self.dismiss_open_popup), size_hint = (0.9, 0.9), auto_dismiss = True)
		self.open_popup.open()


	def load(self, path, filename, *args):
		load_failed_popup = Popup(title = 'Error while opening file', content = Label(text = 'Please select a valid file'), size_hint = (0.8,0.2))
		if filename == []:
			self.dismiss_open_popup()
			load_failed_popup.open()
		else:
			name, extension = os.path.splitext(filename[0])
			if extension == [u'.mi2log'][0]:
				with open(os.path.join(path, filename[0])) as stream:
					t = Thread(target = self.openFile, args=(path, self.selectedTypes))
					t.start()
					self.dismiss_open_popup()
			else:
				self.dismiss_open_popup()
				load_failed_popup.open()


	def openFile(self, Paths,selectedTypes):
		self._log_analyzer.AnalyzeFile(Paths,selectedTypes)


	def OnReadComplete(self):
		self.data =  self._log_analyzer.msg_logs
		self.data_view = self.data
		self.SetUpGrid(self.data_view, len(self.data_view))
		self.loaded = 'Yes'


	def SetUpGrid(self, data, rows):
		self.ids.grid.bind(minimum_height=self.ids.grid.setter('height'))
		self.ids.grid.clear_widgets()
		self.ids.grid.add_widget(Label(text='', size_hint_x = 0.2))
		self.ids.grid.add_widget(Label(text= 'Timestamp' + '      ' + 'Type ID'))
		for i in range(0,rows):
			self.ids.grid.add_widget(Label(text=str(i+1), size_hint_x = 0.2))
			self.ids.grid.add_widget(Button(text = str(data[i]["Timestamp"]) + '      ' + str(data[i]["TypeID"]), on_release = self.grid_popup, id = str(data[i]["Payload"])))


	def grid_popup(self,data):
		val = xml.dom.minidom.parseString(data.id)
		pretty_xml_as_string = val.toprettyxml(indent="  ",newl="\n")
		popup = Popup(title = 'Time Stamp : %s    Type : %s' %(str.split(data.text)[0], str.split(data.text)[1]), content = TextInput(text = pretty_xml_as_string), size_hint = (0.8,0.8))
		popup.open()


############################# Filter
# Pick certain Type IDs to view
# To reset everything, press the Reset button


	def onFilter(self):
		popup = BoxLayout(orientation = 'vertical', size = self.size, pos= self.pos)
		self.filter_popup = Popup(title = 'Filter', content = popup, size_hint = (0.9,0.9), auto_dismiss = True)
		scroll = ScrollView()
		checkbox = GridLayout(cols = 2, row_force_default = True, row_default_height = self.height/20, size_hint_y = None)
		checkbox.bind(minimum_height=checkbox.setter('height'))
		cancel = Button(text = 'Cancel', on_release = self.dismiss_filter_popup)
		ok = Button(text = 'Ok', on_release = self.filter_ok)
		buttons = BoxLayout(size_hint_y = None, height = self.height/20)
		buttons.add_widget(cancel)
		buttons.add_widget(ok)
		scroll.add_widget(checkbox)
		popup.add_widget(scroll)
		popup.add_widget(buttons)
		self.filter_rows = {}
		for i in range(len(self._log_analyzer.supported_types)):
			self.filter_rows[i] = CheckBox(size_hint_x = 0.2)
			checkbox.add_widget(self.filter_rows[i])
			checkbox.add_widget(Label(text=str(list(self._log_analyzer.supported_types)[i])))
		self.filter_popup.open()


	def filter_ok(self, *args):
		if self.loaded == 'Yes':
			self.selectedtypes = []
			for i in range(len(self._log_analyzer.supported_types)):
				if self.filter_rows[i].active == True:
					self.selectedtypes += [list(self._log_analyzer.supported_types)[i]]
			if not self.selectedtypes == []:
				self.data_view = [x for x in self.data_view if x["TypeID"] in self.selectedtypes]
				self.SetUpGrid(self.data_view, len(self.data_view))
			self.dismiss_filter_popup()
		else:
			self.dismiss_filter_popup()


############################# Search
# Search for a keyword in the Payload that shows up when a row is pressed
# To reset everything, press the Reset button


	def onSearch(self):
		popup = BoxLayout(orientation = 'vertical', size = self.size, pos= self.pos)
		self.search_popup = Popup(title = 'Search', content = popup, size_hint = (0.9,0.25), auto_dismiss = True)
		self.search_textinput = TextInput()
		cancel = Button(text = 'Cancel', on_release = self.dismiss_search_popup)
		ok = Button(text = 'Ok', on_release = self.search_ok)
		buttons = BoxLayout(size_hint_y = None, height = self.height/20)
		buttons.add_widget(cancel)
		buttons.add_widget(ok)
		popup.add_widget(self.search_textinput)
		popup.add_widget(buttons)
		self.search_popup.open()


	def search_ok(self, *args):
		if self.loaded == 'Yes':
			self.data_view = [x for x in self.data_view if self.textinput.text in x["Payload"]]
			self.SetUpGrid(self.data_view, len(self.data_view))
			self.dismiss_search_popup()
		else:
			self.dismiss_search_popup()


############################# Reset
# Reset the grid to the state before filtering and/or searching


	def onReset(self):
		if self.loaded == 'Yes':
			self.SetUpGrid(self.data_view, len(self.data_view))
		else:
			pass


#############################


class LogViewerApp(App):
	screen = ObjectProperty(None)
	def build(self):
		self.screen = Window()
		return self.screen

if __name__ == "__main__":
	LogViewerApp().run()
