from . import MobileInsightScreenBase
from kivy.lang import Builder
import main_utils
from kivy.utils import platform

Builder.load_file('screens/about.kv')

class AboutScreen(MobileInsightScreenBase):
    about_text = 'MobileInsight ' + main_utils.get_cur_version()
    pass
