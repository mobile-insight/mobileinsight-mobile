#!/usr/bin/python
# Filename: icellular_monitor.py
"""
iCellular adaptive monitor

It achieves min-search and non-disruptive search.
To do so, it initiates the manual network search, 
trackes the current scanning process (from MobileInsight), 
and stops the search when necessary.

Author: Yuanjie Li
        Zengwen Yuan
"""

from at_cmd import * 

try: 
    import xml.etree.cElementTree as ET 
except ImportError: 
    import xml.etree.ElementTree as ET

from mobile_insight.analyzer import Analyzer


class IcellularMonitor(Analyzer):

    '''
    Monitoring states
    '''
    # NULL = 0;    #monitoring not started
    # STARTED = 1;    #manual network search is initiated   

    
    def __init__(self, monitor_list=[], at_serial_port="/dev/smd11"):
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
        # self.__monitor_state = self.NULL

        #observed carrier lists: carrier -> [RSRP/RSCP, radio/QoS profile (from Rrc/Nas analyzer)]
        #Passed to the decisions strategy
        self.__observed_list = {}    

        #The following memebers track the currently probed carrier network
        self.__cur_plmn = None #MCC-MNC
        self.__cur_rat = None  #4G or 3G
        self.__cur_radio_quality = None  #RSRP or RSCP

        self.__is_network_inaccessible = False   # fault prevention case I
        self.__is_csfb_unavailable = False       # fault prevention case II
        self.__is_selection_unstable = False     # fault prevention case III


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
        for field in msg.iter('field'):
            if field.get('name') == "lte-rrc.systemInformationBlockType1_element":
                return True
        return False

    def __is_wcdma_mib(self,msg):

        '''
        Detect if a WCDMA RRC message is MIB (for MCC/MNC and access barring option)

        :returns: True if it is MIB, False otherwise
        '''
        for field in msg.iter('field'):
            if field.get('name') == "rrc.MasterInformationBlock_element":
                return True
        return False

    def __parse_lte_plmn(self,msg):
        '''
        Given LTE SIB1, parse its MCC/MNC

        :param msg: a xml message that is LTE SIB1
        :returns: a string of "MCCMNC"
        '''
        #WARNING: this code assumes msg is a SIB1, otherwise its behavior is unpredictable!!!
        res=""
        for field in msg.iter('field'):
            if field.get('name') == "lte-rrc.MCC_MNC_Digit":
                res=res+field.get('show')
        return res

    def __parse_wcdma_plmn(self,msg):
        '''
        Given WCDMA MIB, parse its MCC/MNC

        :param msg: a xml message that is WCDMA MIB
        :returns: a string of "MCCMNC"
        '''
        #WARNING: this code assumes msg is a SIB1, otherwise its behavior is unpredictable!!!
        res=""
        for field in msg.iter('field'):
            if field.get('name') == "rrc.Digit":
                res=res+field.get('show')
        return res
        
    def __is_network_inaccessible(self, msg):
        """
        # case I (Forbidden access)
        find in RRC SIB, indicated by access_baring_option == True
        for LTE RRC message retrieve ac-Barring info in the sib2

        """
        self.__is_network_inaccessible = False

        for field in msg.iter('field'):
            # if field.get('name') == "lte-rrc.sib2_element":
            if field.get('name') == "lte-rrc.ac_BarringInfo_element":
                field_val = {}

                # remember to set to the default value based on TS36.331
                field_val['lte-rrc.ac_BarringForEmergency'] = False #mandatory
                field_val['lte-rrc.ac_BarringForMO_Signalling'] = False #optional
                field_val['lte-rrc.ac_BarringForMO_Data'] = False #optional
                field_val['lte-rrc.ac_BarringForCSFB_r10'] = False #optional

                for val in field.iter('field'):
                    field_val[val.get('name')] = val.get('show')

                acBarringForEmergency = bool(field_val['lte-rrc.ac_BarringForEmergency'])
                acBarringForMOSignalling = bool(field_val['lte-rrc.ac_BarringForMO_Signalling'])
                acBarringForMOData = bool(field_val['lte-rrc.ac_BarringForMO_Data'])
                acBarringForCSFB = bool(field_val['lte-rrc.ac_BarringForCSFB_r10'])

                self.__is_network_inaccessible = (acBarringForEmergency
                                                or acBarringForMOSignalling
                                                or acBarringForMOData
                                                or acBarringForCSFB)

    def __is_csfb_unavailable(self, msg):
        """
        # case II (Switch to carriers with incomplete service)
        find in TAU, to see if it is CS-only or CS-preferred
        then we have to see if the current carrier's 3G service
        supports or not (e.g. RSCP <= -95 dBm)
        """
        self.__is_csfb_unavailable = False
        self.__csfb_pref_for_eutran = False

        for field in msg.iter('field'):
            if "Voice domain preference" in field.get('show'):
                for val in field.iter('field'):
                    if val.get('name') == 'gsm_a.gm.gmm.voice_domain_pref_for_eutran' and (("CS Voice only" or "prefer CS Voice") in val.get('show')):
                        self.__csfb_pref_for_eutran = True
                        break

        # when this func is called in the 4G case, we should check the radio_quality for the neighboring 3G cells
        if self.__voice_domain_pref_for_eutran == True:
            for cell in self.__observed_list.keys():
                if "3G" in cell: # neighbor 3G cell radio quality
                    if int(self.__observed_list.get(cell, "0")) < -95: # get(key, default=None)
                        self.__is_csfb_unavailable = True

    def __is_selection_unstable(self, msg):
        """
        # case III (Incoordination with carrier's mobility rules)
        use the cell reselection rule to decide whether a switch
        will trigger unwanted subsequent switches
        """

    def __active_monitor(self, msg):

        '''
        Callback to implement min monitor.
        It monitors the RRC SIB in manual network search, 
        and stops the icellular monitor if search finishes
        '''
        

        print "__active_monitor"
        if not self.__at_cmd.is_running():
            #No AT command is running. Restart the monitoring
            self.run_monitor()
            #Ignore the current messages

        elif msg.type_id == "LTE_RRC_OTA_Packet":
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

            if self.__is_lte_sib1(log_xml):
                self.__cur_plmn=self.__parse_lte_plmn(log_xml) #MCC-MNC
                self.__cur_rat="4G"
                self.__cur_radio_quality=None  #4G RSRP

            self.__is_network_inaccessible(log_xml)

        elif msg.type_id == "WCDMA_Signaling_Messages":
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

            if self.__is_wcdma_mib(log_xml):
                self.__cur_plmn=self.__parse_wcdma_plmn(log_xml) #MCC-MNC
                self.__cur_rat="3G"
                self.__cur_radio_quality=None  #3G RSCP

            self.__is_csfb_unavailable(log_xml)

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
            elif self.__cur_rat == "3G":
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








    

    







