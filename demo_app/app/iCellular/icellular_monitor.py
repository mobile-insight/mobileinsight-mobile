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

from mobile_insight.analyzer import Analyzer, LteRrcAnalyzer

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
        print "iCellularMonitor: I am called"
        self.add_source_callback(self.__active_monitor)

        #TODO: add dependency of Rrc/Nas analyzers (for profiling purpose)
        self.include_analyzer("LteRrcAnalyzer",[self.__on_event])

        print "iCellularMonitor: step 1"
        self.__at_cmd = AtCmd(at_serial_port)  # AT command port
        if monitor_list:
            self.__monitor_list = monitor_list
        else:
            self.__monitor_list = []
        # self.__monitor_state = self.NULL

        print "iCellularMonitor: step 2"
        #observed carrier lists: carrier -> [RSRP/RSCP, radio/QoS profile (from Rrc/Nas analyzer)]
        #Passed to the decisions strategy
        self.__observed_list = {}    

        #The following memebers track the currently probed carrier network
        self.__cur_plmn = None #MCC-MNC
        self.__cur_rat = None  #4G or 3G
        self.__cur_radio_quality = None  #RSRP or RSCP

        print "iCellularMonitor: step 3"
        self.__network_inaccessible = False   # fault prevention case I
        self.__csfb_pref_for_eutran = False
        self.__csfb_unavailable = False       # fault prevention case II
        self.__selection_unstable = False     # fault prevention case III

    def __on_event(self, event):
        """
        Triggered by WcdmaRrcAnalyzer and/or LteRrcAnalyzer.
        Push the event to analyzers that depend on RrcAnalyzer

        :param event: the event raised by WcdmaRrcAnalyzer and/or LteRrcAnalyzer.
        :type event: Event
        """
        # e = Event(event.timestamp, "IcellularMonitor", event.data)
        # self.send(e)
        #TODO: migrate old code here
        pass

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

        #Enable EMM/ESM logs
        source.enable_log("LTE_NAS_ESM_Plain_OTA_Incoming_Message")
        source.enable_log("LTE_NAS_ESM_Plain_OTA_Outgoing_Message")
        source.enable_log("LTE_NAS_EMM_Plain_OTA_Incoming_Message")
        source.enable_log("LTE_NAS_EMM_Plain_OTA_Outgoing_Message")


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
        at_res = self.__at_cmd.run_cmd('AT+CRSM=214,28612,0,0,46,\\"A10C800211088102023281022652FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\\"', False)


        # Block inaccessible carriers (AT&T and Verizon)
        # This is achieved by confiugring fobridden PLMN list (FPLMN) on SIM
        # Verizon=311480 AT&T=310410
        at_res = self.__at_cmd.run_cmd('AT+CRSM=214,28539,0,0,12,\\"130184130014FFFFFFFFFFFF\\"', False)

        #Start the AT command and monitor (non-blocking mode)
        at_res = self.__at_cmd.run_cmd('AT+COPS=?', False)

    def __is_lte_sib1(self, msg):
        '''
        Detect if a LTE RRC message is SIB1 (for MCC/MNC and access barring option)

        :returns: True if it is SIB1, False otherwise
        '''
        for field in msg.iter('field'):
            if field.get('name') == "lte-rrc.systemInformationBlockType1_element":
                return True
        return False

    def __is_wcdma_mib(self, msg):

        '''
        Detect if a WCDMA RRC message is MIB (for MCC/MNC and access barring option)

        :returns: True if it is MIB, False otherwise
        '''
        for field in msg.iter('field'):
            if field.get('name') == "rrc.MasterInformationBlock_element":
                return True
        return False

    def __parse_lte_plmn(self, msg):
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

    def __parse_wcdma_plmn(self, msg):
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
        self.__network_inaccessible = False

        # print "iCellular: __is_network_inaccessible() called"

        for field in msg.iter('field'):
            # if field.get('name') == "lte-rrc.sib2_element":
            if field.get('name') == "lte-rrc.ac_BarringInfo_element":

                try:
                    print "icellular_fp: I found lte-rrc.ac_BarringInfo_element for self.__cur_plmn = " + (self.__cur_plmn)
                except:
                    print "icellular_fp: I found lte-rrc.ac_BarringInfo_element, but self.__cur_plmn None Type"


                field_val = {}

                # remember to set to the default value based on TS36.331
                field_val['lte-rrc.ac_BarringForEmergency'] = False #mandatory
                field_val['lte-rrc.ac_BarringForMO_Signalling'] = False #optional
                field_val['lte-rrc.ac_BarringForMO_Data'] = False #optional
                field_val['lte-rrc.ac_BarringForCSFB_r10'] = False #optional

                for val in field.iter('field'):
                    field_val[val.get('name')] = val.get('show')
                    print "icellular_fp: I got " + val.get('name') + "= " + val.get('show')

                acBarringForEmergency = bool(field_val['lte-rrc.ac_BarringForEmergency'])
                acBarringForMOSignalling = bool(field_val['lte-rrc.ac_BarringForMO_Signalling'])
                acBarringForMOData = bool(field_val['lte-rrc.ac_BarringForMO_Data'])
                acBarringForCSFB = bool(field_val['lte-rrc.ac_BarringForCSFB_r10'])

                self.__network_inaccessible = (acBarringForEmergency
                                                or acBarringForMOSignalling
                                                or acBarringForMOData
                                                or acBarringForCSFB)
                break

                print "icellular_fp: self.__is_network_inaccessible = " + self.__is_network_inaccessible + "for self.__cur_plmn = " + self.__cur_plmn

    def __update_csfb_pref(self, msg):
        """
        # case II (Switch to carriers with incomplete service)
        find in TAU, to see if it is CS-only or CS-preferred
        then we have to see if the current carrier's 3G service
        supports or not (e.g. RSCP <= -95 dBm)
        """
        self.__csfb_pref_for_eutran = False

        for field in msg.iter('field'):
            if "Voice domain preference" in field.get('show'):
                for val in field.iter('field'):
                    if val.get('name') == 'gsm_a.gm.gmm.voice_domain_pref_for_eutran':
                        print "icellular_fp: I found Voice domain preference field, pref = " + val.get("show")
                        if (("CS Voice only" or "prefer CS Voice") in val.get('show')):
                            self.__csfb_pref_for_eutran = True
                            print "icellular_fp: I got Voice domain preference pref CSFB = " + val.get('show') + " for self.__cur_plmn = " + self.__cur_plmn
                            break

    def __is_csfb_unavailable(self, msg):
        """
        # case II (Switch to carriers with incomplete service)
        find in TAU, to see if it is CS-only or CS-preferred
        then we have to see if the current carrier's 3G service
        supports or not (e.g. RSCP <= -95 dBm)
        """
        self.__csfb_unavailable = False
        # when this func is called in the 4G case, we should check the radio_quality for the neighboring 3G cells
        # if self.__csfb_pref_for_eutran == True:
        # Create fake case to test following codes
        if self.__csfb_pref_for_eutran == False:
            for cell in self.__observed_list.keys():
                if "3G" in cell: # neighbor 3G cell radio quality
                    print "icellular_fp: I got neighbor 3G cell radio quality = " + self.__observed_list.get(cell)
                    if int(self.__observed_list.get(cell, "0")) < -95: # get(key, default=None)
                        self.__csfb_unavailable = True
                        print "icellular_fp: unfortunately CSFB is not available"

    def __is_selection_unstable(self, msg):
        """
        # case III (Incoordination with carrier's mobility rules)
        use the cell reselection rule to decide whether a switch
        will trigger unwanted subsequent switches
        """
        pass

    def __active_monitor(self, msg):

        '''
        Callback to implement min monitor.
        It monitors the RRC SIB in manual network search, 
        and stops the icellular monitor if search finishes
        '''
        
        # print "iCellularMonitor: step 4"

        if not self.__at_cmd.is_running():
            #No AT command is running. Restart the monitoring
            self.run_monitor()
            #Ignore the current messages

            print "iCellularMonitor: step 5"

        elif msg.type_id == "LTE_RRC_OTA_Packet":
            '''
            Monitor incoming SIB, detect the currently available carrier network.
            Run the decision-fault prevention function. 
            If the new carrier network available, raise events to downstream analyzer
            (i.e., decision strategy)
            '''

            print "iCellular: __active_monitor.LTE"

            #Convert msg to xml format
            log_item = msg.data.decode()
            log_item_dict = dict(log_item)
            if 'Msg' not in log_item_dict:
                return
            log_xml = ET.XML(log_item_dict['Msg'])

            # print "iCellular: __active_monitor.LTE -- decoded"

            if self.__is_lte_sib1(log_xml):
                self.__cur_plmn=self.__parse_lte_plmn(log_xml) #MCC-MNC
                self.__cur_rat="4G"
                self.__cur_radio_quality=None  #4G RSRP

                print "iCellular: __active_monitor.LTE -- is sib1? called"
                print "iCellular: __active_monitor.LTE -- self.__cur_plmn = " + self.__cur_plmn

            # print "iCellular: __active_monitor.LTE -- calling LteRrcAnalyzer"
            # print str(self.get_analyzer("LteRrcAnalyzer").get_cur_cell_config())
            '''
            02-20 17:14:12.936  1497  1510 I python  : iCellular: __active_monitor.LTE -- calling LteRrcAnalyzer
            02-20 17:14:12.936  1497  1510 I python  : <mobile_insight.analyzer.lte_rrc_analyzer.LteRrcConfig instance at 0xe0098b98>
            02-20 17:14:12.940  1497  1510 I python  : Traceback (most recent call last):
            02-20 17:14:12.940  1497  1510 I python  :   File "/data/user/0/edu.ucla.cs.wing.mobile_insight2/files/app/icellular/main.mi2app", line 41, in <module>
            02-20 17:14:12.940  1497  1510 I python  :     src.run()
            02-20 17:14:12.940  1497  1510 I python  :   File "/home/dale/android/python-for-android-old_toolchain/build/python-install/lib/python2.7/site-packages/mobile_insight/monitor/android_dev_diag_monitor.py", line 321, in run
            02-20 17:14:12.940  1497  1510 I python  :   File "/home/dale/android/python-for-android-old_toolchain/build/python-install/lib/python2.7/site-packages/mobile_insight/element.py", line 38, in send
            02-20 17:14:12.940  1497  1510 I python  :   File "/home/dale/android/python-for-android-old_toolchain/build/python-install/lib/python2.7/site-packages/mobile_insight/analyzer/analyzer.py", line 240, in recv
            02-20 17:14:12.940  1497  1510 I python  :   File "/home/dale/android/python-for-android-old_toolchain/build/python-install/lib/python2.7/site-packages/mobile_insight/analyzer/protocol_analyzer.py", line 94, in __update_state
            02-20 17:14:12.940  1497  1510 I python  : ValueError: dictionary update sequence element #0 has length 1; 2 is required
            '''

            self.__is_network_inaccessible(log_xml)
            print "iCellular: __active_monitor -- updated __is_network_inaccessible = " + str(self.__network_inaccessible)

        elif msg.type_id.startswith("LTE_NAS"):
        # elif msg.type_id == "LTE_NAS_ESM_Plain_OTA_Incoming_Message" \
        #     or msg.type_id == "LTE_NAS_ESM_Plain_OTA_Outgoing_Message" \
        #     or msg.type_id == "LTE_NAS_EMM_Plain_OTA_Incoming_Message" \
        #     or msg.type_id == "LTE_NAS_EMM_Plain_OTA_Outgoing_Message":  
            '''
            Monitor outgoing NAS, detect the voice preference.
            Run the decision-fault prevention function.
            '''

            #Convert msg to xml format
            log_item = msg.data.decode()
            log_item_dict = dict(log_item)
            log_xml = ET.XML(log_item_dict['Msg'])

            print "iCellular: __active_monitor." + str(msg.type_id)

            self.__update_csfb_pref(log_xml)
            print "iCellular: __active_monitor -- updated voice_domain_pref_for_eutran = " + str(self.__csfb_pref_for_eutran)


        elif msg.type_id == "WCDMA_Signaling_Messages":
            '''
            Monitor incoming SIB, detect the currently available carrier network.
            Run the decision-fault prevention function. 
            If the new carrier network available, raise events to downstream analyzer
            (i.e., decision strategy)
            '''

            print "iCellular: __active_monitor.WCDMA"

            #Convert msg to xml format
            log_item = msg.data.decode()
            log_item_dict = dict(log_item)
            if 'Msg' not in log_item_dict:
                return
            log_xml = ET.XML(log_item_dict['Msg'])

            if self.__is_wcdma_mib(log_xml):
                self.__cur_plmn=self.__parse_wcdma_plmn(log_xml) #MCC-MNC
                self.__cur_rat="3G"
                self.__cur_radio_quality=None  #3G RSCP

                try:
                    print "iCellular: __active_monitor.WCDMA -- self.__cur_plmn = " + str(self.__cur_plmn)
                except:
                    print "iCellular: __active_monitor.WCDMA -- self.__cur_plmn None Type ***"

        elif msg.type_id == "Modem_debug_message":
            '''
            Extract RSRP/RSCP from each candidate, map it to the cell
            '''

            print "iCellular: __active_monitor.Modem"

            log_item = msg.data.decode()
            log_item_dict = dict(log_item)

            if self.__cur_rat == "4G":
                #Track RSRP
                index = msg.log_item_dict['Msg'].find("BPLMN LOG: Saved measurement results. rsrp=")
                if index != -1:
                    #LTE RSRP value (in dBm)
                    self.__cur_radio_quality=msg.log_item_dict['Msg'][index:]

                    #TODO: Zengwen, please run decision fault function here
                    self.__is_csfb_unavailable(log_xml)

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

