'''
Screens
=======

.. versionadded:: 5.0.0

Contains all available screens for the Mobile-Insight app.

TODO: more doc

'''

from coordinator import COORDINATOR
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import Screen

Builder.load_string('''
<MobileInsightScreenBase>:
    ScrollView:
        do_scroll_x: False
        do_scroll_y: False
''')


class MobileInsightScreenBase(Screen):
    fullscreen = BooleanProperty(False)

    def __init__(self, **kw):
        super(MobileInsightScreenBase, self).__init__(**kw)
        self.coordinator = COORDINATOR
        self.configure_coordinator()
        Logger.info('screen: screen inited: ' + repr(self))
        ''' TODO:
        currently monitor doesn't support runtime adding analyzers
        after upstream monitor supports this, we can
        start sending control message per screen
        '''
        # self.coordinator.start()

    def configure_coordinator(self):
        '''
        Screens should override this method to setup the coordinator.
        1. specify monitor, analyzers name to the monitor
        2. register callback to analyzers to retrieve data for display
        '''
        # TODO: uncomment this when done all screens
        # raise NotImplementedError
        pass


from .radio import RadioScreen
from .connectivity import ConnectivityScreen
from .dataplane import DataplaneScreen
from .datavoice import DatavoiceScreen
from .mobility import MobilityScreen
from .theming import ThemingScreen
from .home import HomeScreen
from .logviewer import LogViewerScreen
from .about import AboutScreen
from .help import HelpScreen
from .privacy import PrivacyScreen
from .plugins import PluginsScreen

# WARNING: The ordering of the following screens should be consistent with those in mobileinsight.kv (app.go_screen(idx))
__all__ = [
    'HomeScreen', 'PluginsScreen', 'LogViewerScreen', 'HelpScreen', 'AboutScreen', 'PrivacyScreen',
    'RadioScreen', 'ConnectivityScreen', 'DataplaneScreen',
    'DatavoiceScreen', 'MobilityScreen', 'ThemingScreen',
]
