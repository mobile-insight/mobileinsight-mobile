import kivy
kivy.require('1.4.0')

from kivy.uix.screenmanager import Screen
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
from kivy.effects.scroll import ScrollEffect
from kivy.factory import Factory
from kivy.graphics import *
from kivy.properties import ObjectProperty, StringProperty
from kivy.core.window import Window

from mobile_insight.analyzer import LogAnalyzer
from mobile_insight.monitor.dm_collector.dm_endec.dm_log_packet import DMLogPacket

from datetime import datetime, timedelta
from threading import Thread

#import json
import time
import os
import sys
import xml.dom.minidom
#import xmltodict
#import json, xmljson
#from lxml.etree import fromstring, tostring

__all__=["LogViewerScreen"]

#############################

#Window.clearcolor = (1,1,1,1)


Builder.load_string('''
<LogViewerScreen>:
	grid: grid
	btn_grid: btn_grid
	scrrr: scrrr
	GridLayout:
		Button:
			id: open
			text: 'Open'
			size: root.width*0.19, root.height*0.05
			pos: 0, root.height*0.95
			on_release: root.onOpen()
		Button:
			text: 'Filter'
			size: root.width*0.19, root.height*0.05
			pos: root.width*0.2025, root.height*0.95
			on_release: root.onFilter()
		Button:
			text: 'Search'
			size: root.width*0.19, root.height*0.05
			pos: root.width*0.405, root.height*0.95
			on_release: root.onSearch()
		Button:
			text: 'Reset'
			size: root.width*0.19, root.height*0.05
			pos: root.width*0.6075, root.height*0.95
			on_release: root.onReset()
		Button:
			text: 'GoBack'
			size: root.width*0.19, root.height*0.05
			pos: root.width*0.81, root.height*0.95
			on_release: app.manager.current = 'MobileInsightScreen'##########################
		GridLayout:
			pos: 0, root.height*0.9
			size: root.width, root.height/20
			cols: 2
			row_force_default: True
			row_default_height: root.height/20
			Button:
				text:'No.'
				size_hint_x: 0.1
			Button:
				text: 'Timestamp' + '                                 ' + 'Type ID'
				text_size: root.width*0.9, root.height*0.05
				halign: 'left'
				valign: 'middle'
		ScrollView:
			id: scrrr
			size: root.width, root.height*0.9
			GridLayout:
				id: grid
				cols: 2
				row_force_default: True
				row_default_height: root.height/20
				size_hint_y: None
				GridLayout:
					id: btn_grid
					cols: 2
					row_force_default: True
<Open_Popup>:
	BoxLayout:
		size: root.size
		pos: root.pos
		orientation: "vertical"
		FileChooserListView:	
			id: filechooser
			filters: ['/*.mi2log']
			path: '/sdcard/mobile_insight/log'###############################################
			on_selection: root.load(filechooser.path, filechooser.selection, *args)
			minimum_height: filechooser.setter('height')
''')

#Clock.max_iteration = 30

############################# Used for filechooser


class Open_Popup(FloatLayout):
	load = ObjectProperty(None)
	cancel = ObjectProperty(None)


#############################


class LogViewerScreen(Screen):
	cancel = ObjectProperty(None)
	loaded = ObjectProperty(None)
	loadinggrid = ObjectProperty(None)
	ok = ObjectProperty(None)
	ReadComplete = ObjectProperty(None)


	def __init__(self, name): #########################################################
		super(LogViewerScreen, self).__init__()
		self._log_analyzer = LogAnalyzer(self.OnReadComplete)
		self.selectedTypes = None
		self.name = name ##################################################################
		Clock.schedule_interval(self.SetInitialGrid, 0.5)


	def SetInitialGrid(self, *args):
		if self.ReadComplete == 'Yes':
			self.ReadComplete = ''
			self.loaded = 'Yes'
			self.scrrr.effect_y = ScrollEffect()
			self.onReset()


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
				self.loading_num = 2
				self.loading_popup = Popup(title = '', content = Label(text = 'Loading.', font_size = self.width/25), size_hint = (0.3,0.2), separator_height = 0, title_size = 0)
				self.loading_popup.open()
				Clock.schedule_interval(self.loading, 1)
				Clock.unschedule(self.opo)
				self.grid.clear_widgets()
				with open(os.path.join(path, filename[0])) as stream:
					t = Thread(target = self.openFile, args = (os.path.join(path, filename[0]), self.selectedTypes))
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
		self.ReadComplete = 'Yes'


	def opo(self, *args):
		if not self.loadinggrid == 'Yes':
			Move = ''
			rows = len(self.data_view)
			#print self.scrrr.vbar[0]
			scrolltop =  self.scrrr.vbar[0] + self.scrrr.vbar[1]
			scrollbottom = self.scrrr.vbar[0]
			if rows <=50:
				nrows = rows
			else:
				nrows = 50
			if scrolltop >= 1 and self.k != 0:
				Move = 'up'
				self.SetUpGrid(self.data_view, rows, Move)
			if scrollbottom <= 0 and self.k != rows-nrows:
				Move = 'down'
				self.SetUpGrid(self.data_view, rows, Move)


	def SetUpGrid(self, data, rows, Move):
		self.grid.bind(minimum_height=self.grid.setter('height'))
		self.grid.clear_widgets()
		if Move == 'init':
			self.k = 0
			print 'init'
		if Move == 'up':
			self.k -= 25
			print 'up'
		if Move == 'down':
			self.k += 25
			print 'down'
		if rows <= self.k+50:
			self.k = rows-50
			Move == 'over'
		if 0 >= self.k:
			self.k = 0
		self.loadinggrid = 'Yes'
		if Move == 'init':
			self.scrrr.scroll_y = 1
		if Move == 'over':
			self.scrrr.scroll_y = 0
		if Move == 'up':
			self.scrrr.scroll_y = 0.21875
		if Move == 'down':
			self.scrrr.scroll_y = 0.78125
		if rows <=50:
			nrows = rows
		else:
			nrows = 50
		for i in range(self.k, self.k+nrows):
			self.grid.add_widget(Label(text=str(i+1), size_hint_x = 0.1, color = (0,0,0,1)))
			self.grid.add_widget(Button(text = str(data[i]["Timestamp"]) + '      ' + str(data[i]["TypeID"]), on_release = self.grid_popup, id = str(data[i]["Payload"]), text_size = (self.width*0.9, self.height*0.05), halign = 'left', valign = 'middle'))
		#print self.k
		self.loadinggrid = 'No'
		if self.loading_num != '':
			Clock.unschedule(self.loading)
			self.loading_popup.dismiss()
			self.loading_num = ''
		

	def grid_popup(self, data):
		val = xml.dom.minidom.parseString(data.id)
		pretty_xml_as_string = val.toprettyxml(indent="  ",newl="\n")
		#print json.dumps(xmltodict.parse(pretty_xml_as_string), indent = 1)
		scroll = ScrollView()
		label = TextInput(text = str(pretty_xml_as_string), readonly = True, size_hint_y = None)
		label.bind(minimum_height = label.setter('height'))
		scroll.add_widget(label)
		popup = Popup(title = 'Time Stamp : %s\nType : %s' %(str.split(data.text)[0], str.split(data.text)[2]), content = scroll, size_hint = (0.8,0.8))
		popup.open()


	def loading(self, *args):
		if self.loading_num == 1:
			self.loading_popup.content = Label(text = 'Loading.', font_size = self.width/25)
		if self.loading_num == 2:
			self.loading_popup.content = Label(text = 'Loading..', font_size = self.width/25)
		if self.loading_num == 3:
			self.loading_popup.content = Label(text = 'Loading...', font_size = self.width/25)
			self.loading_num = 0
		self.loading_num +=1



############################# Filter
# Pick certain Type IDs to view
# To reset everything, press the Reset button


	def onFilter(self):
		popup = BoxLayout(orientation = 'vertical', size = self.size, pos= self.pos)
		self.filter_popup = Popup(title = 'Filter', content = popup, size_hint = (0.9,0.9), auto_dismiss = True)
		scroll = ScrollView()
		checkbox = GridLayout(cols = 2, row_force_default = True, row_default_height = self.height/20, size_hint_y = None)
		checkbox.bind(minimum_height = checkbox.setter('height'))
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
				self.SetUpGrid(self.data_view, len(self.data_view), 'init')
				Clock.unschedule(self.opo)
				Clock.schedule_interval(self.opo, 0.2)
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
			self.data_view = [x for x in self.data_view if self.search_textinput.text in x["Payload"]]
			self.SetUpGrid(self.data_view, len(self.data_view), 'init')
			self.dismiss_search_popup()
			Clock.unschedule(self.opo)
			Clock.schedule_interval(self.opo, 0.2)
		else:
			self.dismiss_search_popup()


############################# Reset
# Reset the grid to the state before filtering and/or searching


	def onReset(self):
		if self.loaded == 'Yes':
			self.SetUpGrid(self.data, len(self.data), 'init')
			Clock.unschedule(self.opo)
			Clock.schedule_interval(self.opo, 0.2)
		else:
			pass


#############################


class LogViewerApp(App):
	screen = ObjectProperty(None)
	def build(self):
		self.screen = LogViewerScreen()
		return self.screen

Factory.register('LogViewerScreen', cls=LogViewerScreen)
Factory.register('Open_Popup', cls=Open_Popup)

if __name__ == "__main__":
	LogViewerApp().run()
