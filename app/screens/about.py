import main_utils
from kivy.lang import Builder

from . import MobileInsightScreenBase

Builder.load_file('screens/about.kv')


class AboutScreen(MobileInsightScreenBase):
    about_text = 'MobileInsight ' + main_utils.get_cur_version() + '\n'
    with open('screens/about.txt', 'r') as content_file:
        content = content_file.read()
        about_text = about_text + content + '\n'
    about_text = about_text + 'copyright (c) 2015 - 2020 by MobileInsight Team'
    pass
