#!/usr/bin/python
import os
import sys

#Import MobileInsight modules
import mobile_insight
from mobile_insight.monitor import QmdlReplayer
from mobile_insight.analyzer import LteRrcAnalyzer

# Initialize a 3G/4G monitor
src = QmdlReplayer({"ws_dissect_executable_path": "/data/likayo/android_pie_ws_dissector",
                    "libwireshark_path": "/data/likayo/"})
src.set_input_path("/sdcard/to_be_read.qmdl")

#RRC analyzer
rrc_analyzer = LteRrcAnalyzer()
rrc_analyzer.set_source(src) #bind with the monitor
rrc_analyzer.set_log("/sdcard/3g-4g-rrc.txt") #save the analysis result

#Start the monitoring
src.run()

app_log = open("/sdcard/3g-4g-rrc.txt").read()[0:1000]