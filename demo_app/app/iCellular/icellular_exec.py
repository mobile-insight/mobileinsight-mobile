#!/usr/bin/python
# Filename: icellular_exec.py
"""
iCellular direct switch

It achieves direct switch and reduces the service interruption time.

Author: Yuanjie Li
"""


from at_cmd import * 

from mobile_insight.analyzer import Analyzer

class IcellularExec(Analyzer):

    def __init__(self, at_serial_port="/dev/smd11"):

        '''
        Initialization

        :at_serial_port: in-phone device that connects to AT command at_serial_port
        :type at_serial_port: string
        '''

        #No MobileInsight monitor callback, but it relies on command from decision strategy
        Analyzer.__init__(self)
        self.include_analyzer("IcellularDecision",[self.__run_switch])

        #FIXME: conflicts with AtCmd in IcellularMonitor
        self.__at_cmd = AtCmd(at_serial_port)  # AT command port

    def set_source(self,source):
        """
        Set the trace source. Enable the LTE RRC messages.

        :param source: the trace source.
        :type source: trace collector
        """
        Analyzer.set_source(self,source)

    def __run_switch(self,msg):
        '''
        Perform inter-carrier selection
        '''
        #TODO: migrate old code here
        pass



