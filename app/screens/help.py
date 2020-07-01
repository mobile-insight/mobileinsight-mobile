from kivy.lang import Builder

from . import MobileInsightScreenBase

Builder.load_file('screens/help.kv')


class HelpScreen(MobileInsightScreenBase):
    about_text = ''
    with open('screens/help.txt', 'r') as content_file:
        content = content_file.read()
        about_text = about_text + content + '\n'
    pass
