from kivy.lang import Builder

from . import MobileInsightScreenBase

Builder.load_file('screens/privacy.kv')


class PrivacyScreen(MobileInsightScreenBase):
    about_text = ''
    with open('privacy_agreement.txt', 'r') as content_file:
        content = content_file.read()
        about_text = about_text + content + '\n'
