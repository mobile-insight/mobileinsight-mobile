#!/usr/bin/python
# Filename: icellular_monitor.py
"""
iCellular adaptive monitor

It achieves min-search and non-disruptive search.
To do so, it initiates the manual network search, 
trackes the current sacnning process (from MobileInsight), 
and stops the search when necessary.

Author: Yuanjie Li
"""

from at_cmd import * 

from mobile_insight.analyzer import Analyzer


class iCellularMonitor(Analyzer):

	'''
	Monitoring states
	'''
	NULL = 0;	#monitoring not started
	STARTED = 1;	#manual network search is initiated   

    
    def __init__(self, monitor_list, at_serial_port):
        '''
        Initialize the iCellular monitor

        :param monitor_list: a list of carriers to be monitored (in MNC/MCC form)
        :type monitor_list: list
        :at_serial_port: in-phone device that connects to AT command at_serial_port
        :type at_serial_port: string
        '''

        #MobileInsight Analyzer init
        Analyzer.__init__(self)
        self.add_source_callback(self.__active_monitor)
        #TODO: add dependency of Rrc/Nas analyzers (for profiling purpose)

        self.__at_cmd = AtCmd(at_serial_port)  # AT command port
        if monitor_list:
            self.__monitor_list = monitor_list
        else:
        	self.__monitor_list = []
        self.__monitor_state = self.NULL

        #observed carrier lists: carrier -> [RSRP/RSCP, radio/QoS profile (from Rrc/Nas analyzer)]
        #Passed to the decisions strategy
        self.__observed_list = {}	

        #Start the active monitor
        self.run_monitor(self.__monitor_list) 	


    def set_source(self,source):
        """
        Set the trace source. Enable the LTE RRC messages.

        :param source: the trace source.
        :type source: trace collector
        """
        Analyzer.set_source(self,source)
        #enable LTE RRC log
        source.enable_log("LTE_RRC_OTA_Packet")
        # source.enable_log("LTE_RRC_Serv_Cell_Info_Log_Packet")
        source.enable_log("Modem_debug_message") #Get RSRP/RSCP in manual network search



    def run_monitor(self, monitor_list):
        '''
        Start the active monitor (called by external source). 
        NOTE: this function is **non-blocking**, i.e., it exits immediately after
        manual network search is initiated.

        :param monitor_list: a list of carriers to be monitored (in MNC/MCC form)
        :type monitor_list: list
        '''
       

        '''
        Stop ongoing AT commands (if any)
	    
	    There is NO available AT commands to do it. 
	    As a work-around, if COPS is running, making a call will terminate the search
	    To make a phone call, DON'T USE ATD command. It does not work
    	'''


        #Reset observed carrier networks
        self.__observed_list = []


        #Configure the preferred carrier list


        # Block inaccessible carriers (AT&T and Verizon)
        at_res = self.__at_cmd.run_cmd("AT+COPS=?", False)

        #Start the AT command and monitor (non-blocking mode)
        #This is achieved by confiugring fobridden PLMN list (FPLMN) on SIM
        #Verizon=311480 AT&T=310410
        at_res = self.__at_cmd.run_cmd("AT+CRSM=214,28539,0,0,12,\"130184130014\"", False)
        self.__monitor_state = self.STARTED


    def __active_monitor(self, msg):

    	'''
    	Callback to implement min monitor.
    	It monitors the RRC SIB in manual network search, 
    	and stops the icellular monitor if search finishes
    	'''



    	if self.__monitor_state == self.NULL:
    	    #No active monitor initiated
    	    return
    	else:
    	    '''
    	    Monitor incoming SIB and RSRP, detect the currently available carrier network.
    	    Run the decision-fault prevention function. 
    	    If the new carrier network available, raise events to downstream analyzer
    	    (i.e., decision strategy)
    	    '''

            #TODO: support 0x1FEB  Extended Debug Message (for RSRP/RSRQ)
            #TODO: build lists
    	    self.send(self.__observed_list) #Currently observed carriers






    

    







