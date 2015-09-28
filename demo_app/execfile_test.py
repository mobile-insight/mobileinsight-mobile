#!/usr/bin/python
# Filename: offline-qmdl-analysis-example.py
import os
import sys

#Import MobileInsight modules
from mobile_insight.monitor import QmdlReplayer
from mobile_insight.analyzer import LteRrcAnalyzer

if __name__ == "__main__":
    
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
