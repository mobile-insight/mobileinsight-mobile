#!/usr/bin/python
# Filename: icellular_analyzer.py
"""
iCellular main analyzer

This module is the "main entrance". 
It integrates the basic monitor->decision->switch flow and background learning

Author: Yuanjie Li
"""


from mobile_insight.analyzer import Analyzer

class IcellularAnalyzer(Analyzer):
    
    def __init__(self):
        print "IcellularAnalyzer is called"
        Analyzer.__init__(self)
        self.include_analyzer("IcellularExec",[]) #NO action, include analyzer only
        # self.include_analyzer("IcellularDecision",[]) #NO action, include analyzer only
        #TODO: include analyzers for background profiling and learning


    def set_source(self,source):
        """
        Set the trace source. 
        :param source: the trace source.
        :type source: trace collector
        """
        Analyzer.set_source(self,source)