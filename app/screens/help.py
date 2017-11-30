from . import MobileInsightScreenBase
from kivy.lang import Builder
import main_utils
from kivy.utils import platform

Builder.load_file('screens/help.kv')

class HelpScreen(MobileInsightScreenBase):
    about_text = ''
    with open('screens/help.txt', 'r') as content_file:
        content = content_file.read()
        about_text =  about_text + content + '\n'
    pass