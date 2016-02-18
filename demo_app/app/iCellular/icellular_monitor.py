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
    NULL = 0;    #monitoring not started
    STARTED = 1;    #manual network search is initiated   

    
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

        #The following memebers track the currently probed carrier network
        self.__cur_plmn=None #MCC-MNC
        self.__cur_rat=None  #4G or 3G
        self.__cur_radio_quality=None  #RSRP or RSCP    


    def set_source(self,source):
        """
        Set the trace source. Enable the LTE RRC messages.

        :param source: the trace source.
        :type source: trace collector
        """
        Analyzer.set_source(self,source)
        #enable LTE RRC log
        source.enable_log("LTE_RRC_OTA_Packet")
        source.enable_log("WCDMA_Signaling_Messages")
        # source.enable_log("LTE_RRC_Serv_Cell_Info_Log_Packet")
        source.enable_log("Modem_debug_message") #Get RSRP/RSCP in manual network search



    def run_monitor(self):
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
        self.__observed_list = {}
        self.__cur_plmn=None #MCC-MNC
        self.__cur_rat=None  #4G or 3G
        self.__cur_radio_quality=None  #RSRP or RSCP


        # Configure the preferred carrier list
        # We configure the pre-stored carrier frequence band (4.2.57, TS31.102)
        # In scanning, the carrier network will only scan the following bands
        # TODO: further optimize the bands. The following config comes from AT&T
        at_res = self.__at_cmd.run_cmd("AT+CRSM=214,28612,0,0,46,\"A10C800211088102023281022652FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\"", False)


        # Block inaccessible carriers (AT&T and Verizon)
        # This is achieved by confiugring fobridden PLMN list (FPLMN) on SIM
        # Verizon=311480 AT&T=310410
        at_res = self.__at_cmd.run_cmd("AT+CRSM=214,28539,0,0,12,\"130184130014FFFFFFFFFFFF\"", False)

        #Start the AT command and monitor (non-blocking mode)
        at_res = self.__at_cmd.run_cmd("AT+COPS=?", False)

    def __is_lte_sib1(self,msg):
        '''
        Detect if a LTE RRC message is SIB1 (for MCC/MNC and access barring option)

        :returns: True if it is SIB1, False otherwise
        '''
        for field in msg.data.iter('field'):
            if field.get('name') == "lte-rrc.systemInformationBlockType1_element":
                return True

    def __parse_lte_plmn(self,msg):
        '''
        Given LTE SIB1, parse its MCC/MNC

        :param msg: a xml message that is LTE SIB1
        :returns: a string of "MCCMNC"
        '''
        #WARNING: this code assumes msg is a SIB1, otherwise its behavior is unpredictable!!!
        res=""
        for field in msg.data.iter('field'):
            if field.get('name') == "lte-rrc.MCC_MNC_Digit":
                res=res+field.get('show')
        return res

    def __is_wcdma_sib(self,msg):
        


    def __active_monitor(self, msg):

        '''
        Callback to implement min monitor.
        It monitors the RRC SIB in manual network search, 
        and stops the icellular monitor if search finishes
        '''

        if not self.__at_cmd.is_running():
            #No AT command is running. Restart the monitoring
            self.run_monitor()
            #Ignore the current messages

        elif msg.type_id == "LTE_RRC_OTA_Packet"::
            '''
            Monitor incoming SIB, detect the currently available carrier network.
            Run the decision-fault prevention function. 
            If the new carrier network available, raise events to downstream analyzer
            (i.e., decision strategy)
            '''

            #Convert msg to xml format
            log_item = msg.data.decode()
            log_item_dict = dict(log_item)
            log_xml = ET.XML(log_item_dict['Msg'])
            xml_msg = Event(msg.timestamp, msg.type_id, log_xml)

            if self.__is_lte_sib1(xml_msg):
                self.__cur_plmn=self.__parse_lte_plmn(xml_msg) #MCC-MNC
                self.__cur_rat="4G"  #4G or 3G
                self.__cur_radio_quality=None  #RSRP or RSCP

        elif msg.type_id == "WCDMA_Signaling_Messages":
            '''
            Monitor incoming SIB, detect the currently available carrier network.
            Run the decision-fault prevention function. 
            If the new carrier network available, raise events to downstream analyzer
            (i.e., decision strategy)
            '''

            #Convert msg to xml format
            log_xml = ET.XML(log_item_dict['Msg'])
            xml_msg = Event(msg.timestamp, msg.type_id, log_xml)

        elif msg.type_id == "Modem_debug_message":
            '''
            Extract RSRP/RSCP from each candidate, map it to the cell
            '''
            log_item = msg.data.decode()
            log_item_dict = dict(log_item)

            if self.__cur_rat == "4G":
                #Track RSRP
                index = msg.log_item_dict['Msg'].find("BPLMN LOG: Saved measurement results. rsrp=")
                if index != -1:
                    #LTE RSRP value (in dBm)
                    self.__cur_radio_quality=msg.log_item_dict['Msg'][index:]
                    #TODO: Zengwen, please run decision fault function here

                    #Send available carrier networks to decision
                    self.__observed_list[self.__cur_plmn+"-"+self.__cur_rat]=self.__cur_radio_quality
                    self.send(self.__observed_list) #Currently observed carriers
                    #Reset current carrier network
                    self.__cur_plmn=None #MCC-MNC
                    self.__cur_rat=None  #4G or 3G
                    self.__cur_radio_quality=None  #RSRP or RSCP
            elif self.__cur_rat == "4G":
                #Track RSCP
                field_list = msg.log_item_dict['Msg'].split(' ')
                for field in field_list:
                    index = field.find("rscp=")
                    if index !=-1:
                        #WCDMA RSCP value (in dBm)
                        self.__cur_radio_quality=msg.log_item_dict['Msg'][index:]

                        #TODO: Zengwen, please run decision fault function here

                        #Send available carrier networks to decision
                        self.__observed_list[self.__cur_plmn+"-"+self.__cur_rat]=self.__cur_radio_quality
                        self.send(self.__observed_list) #Currently observed carriers
                        #Reset current carrier network
                        self.__cur_plmn=None #MCC-MNC
                        self.__cur_rat=None  #4G or 3G
                        self.__cur_radio_quality=None  #RSRP or RSCP








    

    







