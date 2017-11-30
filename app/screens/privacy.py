from . import MobileInsightScreenBase
from kivy.lang import Builder
import main_utils
from kivy.utils import platform

Builder.load_file('screens/privacy.kv')

class PrivacyScreen(MobileInsightScreenBase):
    about_text = ''
    with open('privacy_agreement.txt', 'r') as content_file:
        content = content_file.read()
        about_text =  about_text + content + '\n'