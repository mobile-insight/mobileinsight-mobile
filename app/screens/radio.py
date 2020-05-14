from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import StringProperty

from . import MobileInsightScreenBase

Builder.load_file('screens/radio.kv')


class RadioScreen(MobileInsightScreenBase):
    current_log = StringProperty('')

    def configure_coordinator(self):
        self.coordinator.register_analyzer('LteNasAnalyzer')
        self.coordinator.register_analyzer('LteRrcAnalyzer')
        self.coordinator.register_callback(self._demo_callback)

    def _demo_callback(self, event):
        Logger.info('DemoScreen: ' + str(event))
        string = str(event)
        self.current_log = string[:20]
