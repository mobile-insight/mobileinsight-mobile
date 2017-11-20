# -*- coding: utf-8 -*-

from kivy.lang import Builder
from kivy.properties import ListProperty, OptionProperty, BooleanProperty,NumericProperty,StringProperty
from kivy.utils import get_color_from_hex
from kivymd.color_definitions import colors
from kivymd.theming import ThemableBehavior
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
import random

Builder.load_string('''
#:import get_color_from_hex kivy.utils.get_color_from_hex
#:import MDLabel kivymd.label.MDLabel
<MDProgressBar>:
    canvas:
        Clear
        Color:
            rgba:  self.theme_cls.divider_color
        Rectangle:
            size:    (self.width*0.6, dp(18)) if self.orientation == 'horizontal' else (dp(18),self.height-dp(8))
            pos:   (self.x+self.width*0.2, self.center_y) if self.orientation == 'horizontal' \
                else (self.center_x + dp(24),self.y)


        Color:
            #rgba:  self.theme_cls. primary_color
            #rgba:  self.get_color() if self.test else self.theme_cls. primary_color
            rgba:  get_color_from_hex(self.rgbr)
        Rectangle:
            size:     (self.width*self.value_normalized*0.6, sp(18)) if self.orientation == 'horizontal' else (sp(18), \
                self.height*self.value_normalized)
                #self.width*(1-self.value_normalized)+self.x
            pos:    (self.width*0.6*(1-self.value_normalized)+self.x+self.width*0.2 if self.reversed else self.x+self.width*0.2, self.center_y) \
                if self.orientation == 'horizontal' else \
                (self.center_x + dp(24),self.height*(1-self.value_normalized)+self.y if self.reversed else self.y)
''')


class MDProgressBar(ThemableBehavior, ProgressBar):
    reversed = BooleanProperty(False)
    ''' Reverse the direction the progressbar moves. '''
    orientation = OptionProperty('horizontal', options=['horizontal', 'vertical'])
    ''' Orientation of progressbar'''
    rgbr = StringProperty("FF0000")
    test = BooleanProperty(False)
    #rgbr = OptionProperty('FF0000',
        #options=['FF0000','00FF00','0000FF'])
    alpha =NumericProperty(.9)


    def on_rgbr(self,instance,value):
        # self.rgbr = value
        # print "on_rgbr"
        #print self.rgbr
        r1,r2=153,255
        g1,g2=255,0
        b1,b2=0,0
        r=int((r1*self.value+r2*(100-self.value))/100)
        g=int((g1*self.value+g2*(100-self.value))/100)
        b=int((b1*self.value+b2*(100-self.value))/100)

        self.rgbr= hex(r)[2:].zfill(2)+hex(g)[2:].zfill(2)+hex(b)[2:].zfill(2)
    def on_value(self,instance,value):
        r1,r2=255,153
        g1,g2=0,255
        b1,b2=0,0
        r=int((r1*self.value+r2*(100-self.value))/100)
        g=int((g1*self.value+g2*(100-self.value))/100)
        b=int((b1*self.value+b2*(100-self.value))/100)

        self.rgbr= hex(r)[2:].zfill(2)+hex(g)[2:].zfill(2)+hex(b)[2:].zfill(2)

    # def get_color(self):
    #     color = get_color_from_hex(self.rgbr)
    #     color[3]=self.alpha
    #     print "color"
    #     print color
    #     return color





if __name__ == '__main__':
    from kivy.app import App
    from kivymd.theming import ThemeManager

    class ProgressBarApp(App):
        theme_cls = ThemeManager()
        rvalue = NumericProperty(40)

        def callback(self,dt):
            self.rvalue =random.random()*100
            print self.rvalue
        def on_rvalue(self,instance,value):
             pass


        def build(self):
            Clock.schedule_interval(self.callback, 1)
            return Builder.load_string("""#:import MDSlider kivymd.slider.MDSlider
        #:import MDLabel kivymd.label.MDLabel
BoxLayout:
    orientation:'vertical'
    padding: '8dp'
    MDSlider:
        id:slider
        min:0
        max:100
        value: 10

    MDProgressBar:
        value: app.rvalue
        rgbr:"00FF00"
    MDProgressBar:
        reversed: True
        value: app.rvalue
        rgbr:"00FFFF"
    BoxLayout:
        MDProgressBar:
            orientation:"vertical"
            reversed: False
            value: slider.value
            rgbr:"FFFF00"
            test: True
            alpha:.7

        MDProgressBar:
            orientation:"vertical"
            value: slider.value
            reversed:True
            rgbr:"00ff77"

        MDLabel:
            text: str(app.rvalue)
            theme_text_color: 'Primary'
            font_style:"Caption"
            size_hint_y: None
            halign: 'center'
            height: self.texture_size[1] + dp(64)



""")


    ProgressBarApp().run()
