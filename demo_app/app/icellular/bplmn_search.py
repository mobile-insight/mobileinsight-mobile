#!/usr/bin/python
# Filename: bplmn-search.py

"""
A background PLMN search module. Help reduce unavailability PLMN search overhead

Author: Yuanjie Li
        Zengwen Yuan
"""

import time
import thread
import threading

from at_cmd import * 

try: 
    import xml.etree.cElementTree as ET 
except ImportError: 
    import xml.etree.ElementTree as ET
from mobile_insight.analyzer import *
from mobile_insight.protocol_analyzer import *
import timeit

# from mobile_insight.profile import Profile, ProfileHierarchy

#ESM session connection state
esm_state={0:"disconnected",1:"connected"}

#QoS mapping: 10.5.6.5, TS24.008
mean_tput={1:100,2:200,3:500,4:1000,5:2000,6:5000,7:10000,8:20000,
        9:50000,10:100000,11:200000,12:500000,13:1000000,14:2000000,
        15:5000000,16:10000000,17:20000000,18:50000000,31:"best effort"}


delivery_order={1:"with delivery order", 2:"without delivery order"}


traffic_class={1:"conversional class", 2:"streaming class",
        3:"interactive class", 4:"background class"}


residual_ber={1:5e-2, 2:1e-2, 3:5e-3, 4:4e-3, 5:1e-3, 6:1e-4, 7:1e-5,
        8:1e-6, 9:6e-8}

def xstr(val):
    '''
    Return a string for valid value, or empty string for Nontype

    :param val: a value
    :returns: a string if val is not none, otherwise an empty string
    '''

    if val:
        return str(val)
    else:
        return "unknown"


def max_bitrate(val):
    '''
    Given ESM value, return maximum bit rate (Kbps).
    Please refer to 10.5.6.5, TS24.008 for more details.

    :param val: the value encoded in the ESM NAS message
    '''
    if val<=63:
        return val
    elif val<=127:
        return 64+(val-64)*8
    elif val<=254:
        return 576+(val-128)*64
    else:
        return 0


def max_bitrate_ext(val):
    """
    Given ESM value, return extended maximum bit rate (Kbps).
    Please refer to 10.5.6.5, TS24.008 for more details.

    :param val: the value encoded in the ESM NAS message
    """
    if val<=74:
        return 8600+val*100
    elif val<=186:
        return 16000+(val-74)*1000
    elif val<=250:
        return 128000+(val-186)*2000
    else:
        return None


def trans_delay(val):
    """
    Given ESM value, return transfer delay (ms).
    Please refer to 10.5.6.5, TS24.008 for more details.

    :param val: the value encoded in the ESM NAS message
    """
    if val<=15:
        return val*10
    elif val<=31:
        return 200+(val-16)*50
    elif val<=62:
        return 1000+(val-32)*100
    else:
        return None

class BplmnItem:

    '''
        Store the BPLMN search result
    '''

    def __init__(self, mode, carrier, mcc_mnc, rat, last_update_time = None):
        self.mode = int(mode)
        self.carrier = carrier
        self.mcc_mnc = mcc_mnc
        self.rat = rat
        if last_update_time is None:
            self.last_update_time = -1
        else:
            self.last_update_time = last_update_time

class LteRrcStatus:
    """
    The metadata of a cell, including its ID, frequency band, tracking area code, 
    bandwidth, connectivity status, etc.
    """
    def __init__(self):
        self.id = None #cell ID
        self.freq = None #cell frequency
        self.rat = "LTE" #radio technology
        self.tac = None #tracking area code
        self.mcc = None #Mobile Country Codes (MCC)
        self.mnc = None #Mobile Network Codes (MNC)
        self.mcc_mnc = None
        self.bandwidth = None #cell bandwidth
        self.conn = False #connectivity status (for serving cell only)

    def dump(self):
        """
        Report the cell status

        :returns: a string that encodes the cell status
        :rtype: string
        """
        return (self.__class__.__name__
            + " carrier(mcc_mnc)=" + str(self.mcc + self.mnc)
            + " cellID=" + str(self.id)
            + " frequency=" + str(self.freq)
            + " TAC=" + str(self.tac)
            + " connected=" + str(self.conn) + '\n')

    def inited(self):
        # return (self.id!=None and self.freq!=None)
        return (self.id and self.freq)

class EsmStatus:
    """
    An abstraction to maintain the ESM status
    """
    def __init__(self):
        self.qos = EsmQos()

        # # test profile
        # self.id=None

class EsmQos:
    """
    An abstraction for ESM QoS profiles
    """
    def __init__(self):
        # self.qci=None
        self.delay_class=None
        self.reliability_class=None
        self.precedence_class=None
        self.peak_tput=None
        self.mean_tput=None
        self.traffic_class=None
        self.delivery_order=None
        self.transfer_delay=None
        self.traffic_handling_priority=None
        self.max_bitrate_ulink=None
        self.max_bitrate_dlink=None
        self.guaranteed_bitrate_ulink=None
        self.guaranteed_bitrate_dlink=None
        self.max_bitrate_ulink_ext=None
        self.max_bitrate_dlink_ext=None
        self.guaranteed_bitrate_ulink_ext=None
        self.guaranteed_bitrate_dlink_ext=None
        self.residual_ber=None

    def dump_rate(self):
        """
        Report the data rate profile in ESM QoS, including the peak/mean throughput,
        maximum downlink/uplink data rate, guaranteed downlink/uplink data rate, etc.

        :returns: a string that encodes all the data rate 
        :rtype: string
        """
        # print self.__class__.__name__,"Throughput(Kbps):",self.peak_tput,self.mean_tput, \
        # self.max_bitrate_ulink, self.max_bitrate_dlink, \
        # self.guaranteed_bitrate_ulink, self.guaranteed_bitrate_dlink, \
        # self.max_bitrate_ulink_ext, self.max_bitrate_dlink_ext, \
        # self.guaranteed_bitrate_ulink_ext, self.guaranteed_bitrate_dlink_ext
        return (self.__class__.__name__ 
            + ' peak_tput=' + xstr(self.peak_tput) + ' mean_tput=' + xstr(self.mean_tput)
            + ' max_bitrate_ulink=' + xstr(self.max_bitrate_ulink) + ' max_bitrate_dlink=' + xstr(self.max_bitrate_dlink)
            + ' guaranteed_birate_ulink=' + xstr(self.guaranteed_bitrate_ulink) + ' guaranteed_birate_dlink=' + xstr(self.guaranteed_bitrate_dlink)
            + ' max_bitrate_ulink_ext=' + xstr(self.max_bitrate_ulink_ext) + ' max_bitrate_dlink_ext=' + xstr(self.max_bitrate_dlink_ext)
            + ' guaranteed_birate_ulink_ext=' + xstr(self.guaranteed_bitrate_ulink_ext) + ' guaranteed_birate_dlink_ext=' + xstr(self.guaranteed_bitrate_dlink_ext))

    def dump_delivery(self):
        """
        Report the delivery profile in ESM QoS, including delivery order guarantee,
        traffic class, QCI, delay class, transfer delay, etc.

        :returns: a string that encodes all the data rate, or None if not ready 
        :rtype: string
        """
        if self.delivery_order:
            order = delivery_order[self.delivery_order]
        else:
            order = None
        if self.traffic_class:
            tra_class = traffic_class[self.traffic_class]
        else:
            tra_class = None
        return (self.__class__.__name__
            + ' delivery_order=' + xstr(order)
            + ' traffic_class=' + xstr(tra_class)
            + ' QCI=' + xstr(self.qci) + ' delay_class=' + xstr(self.delay_class)
            + ' transfer_delay=' + xstr(self.transfer_delay) + ' residual_BER=' + xstr(self.residual_ber))

class MmNasStatus:
    """
    An abstraction to maintain the MM NAS status.
    """
    def __init__(self):

        self.qos_negotiated.delay_class = None
        self.qos_negotiated.reliability_class = None
        self.qos_negotiated.peak_throughput = None
        self.qos_negotiated.precedence_class = None
        self.qos_negotiated.mean_throughput = None
        self.qos_negotiated.traffic_class = None
        self.qos_negotiated.delivery_order = None
        self.qos_negotiated.traffic_handling_priority = None
        self.qos_negotiated.residual_ber = None
        self.qos_negotiated.transfer_delay = None
        self.qos_negotiated.max_bitrate_ulink = None
        self.qos_negotiated.max_bitrate_dlink = None
        self.qos_negotiated.guaranteed_bitrate_ulink = None
        self.qos_negotiated.guaranteed_bitrate_dlink = None
        self.qos_negotiated.max_bitrate_dlink_ext = None
        self.qos_negotiated.guaranteed_bitrate_dlink_ext = None

class BplmnSearch(Analyzer):

    def __init__(self, at_serial_port):

        '''
            Initialize the search daemon

            :param at_serial_port: the serial port that can be used to send AT command 
        '''

        self.current_network_inaccessible = False
        self.voice_domain_pref_for_eutran = None
        self.wcdma_available = False # for case II decision part

        # TODO: call other analyzer to parse the msg
        # self.include_analyzer("WcdmaRrcAnalyzer",[self.__on_wcdma_rrc_msg])
        # self.include_analyzer("LteRrcAnalyzer",[self.__on_lte_rrc_msg])
        # self.include_analyzer("LteNasAnalyzer",[self.__on_lte_nas_msg])
        # self.include_analyzer("UmtsNasAnalyzer",[self.__on_umts_nas_msg])

        Analyzer.__init__(self)
        self.add_source_callback(self.__rrc_filter)
        self.add_source_callback(self.__nas_filter)

        self.at_cmd = AtCmd(at_serial_port)

        #init internal states
        self.__status = LteRrcStatus()    # current cell status
        self.__esm_status = EsmStatus()
        self.__mm_nas_status = MmNasStatus()

        self.bplmn_database = {}  # Carrier -> Availability
        self.last_update_time = -1 # last time to update bplmn result. -1 means not available
        self.lock = thread.allocate_lock() # a lock between monitor and decision

    def __nas_filter(self, msg):
        """
        Filter all NAS(EMM/ESM) packets, and call functions to process it

        :param msg: the event (message) from the trace collector.
        """

        if msg.type_id == "LTE_NAS_ESM_Plain_OTA_Incoming_Message" \
        or msg.type_id == "LTE_NAS_ESM_Plain_OTA_Outgoing_Message" \
        or msg.type_id == "LTE_NAS_EMM_Plain_OTA_Incoming_Message" \
        or msg.type_id == "LTE_NAS_EMM_Plain_OTA_Outgoing_Message" \
        or msg.type_id == "UMTS_NAS_OTA":   
            # log_item = msg.data
            log_item = msg.data.decode()
            log_item_dict = dict(log_item)

            # if not log_item_dict.has_key('Msg'):
            if 'Msg' not in log_item_dict:
                return

            #Convert msg to xml format
            # log_xml = ET.fromstring(log_item_dict['Msg'])
            log_xml = ET.XML(log_item_dict['Msg'])
            xml_msg = Event(msg.timestamp, msg.type_id, log_xml)

            # check if CSFB will fail
            self.__voice_preferred_csfb(xml_msg)

            # get the QoS latency and guaranteed bitrate
            if msg.type_id == "UMTS_NAS_OTA":
                self.__callback_umts_nas(xml_msg)
            else:
                self.__callback_esm(xml_msg)
            
            # e = Event(timeit.default_timer(),self.__class__.__name__,"")
            # self.send(e)
            self.send(xml_msg)

    # moved to the __is_network_unavailable function
    # def __callback_emm(self,msg):
    #     """
    #     Extract EMM status and configurations from the NAS messages

    #     :param msg: the EMM NAS message
    #     """
    #     '''
    #     <field name="" pos="76" show="Voice domain preference and UE's usage setting" size="3" value="5d0100">
    #       <field name="gsm_a.gm.elem_id" pos="76" show="93" showname="Element ID: 0x5d" size="1" value="5d" />
    #       <field name="gsm_a.len" pos="77" show="1" showname="Length: 1" size="1" value="01" />
    #       <field name="gsm_a.spare_bits" pos="78" show="0" showname="0000 0... = Spare bit(s): 0" size="1" value="00" />
    #       <field name="gsm_a.gm.gmm.ue_usage_setting" pos="78" show="0" showname=".... .0.. = UE's usage setting: Voice centric" size="1" value="00" />
    #       <field name="gsm_a.gm.gmm.voice_domain_pref_for_eutran" pos="78" show="0" showname=".... ..00 = Voice domain preference for E-UTRAN: CS Voice only (0)" size="1" value="00" />
    #     </field>
    #     '''
    #     # <proto name="nas-eps" pos="8" showname="Non-Access-Stratum (NAS)PDU" size="79">
    #     for field in msg.data.iter('field'):
    #         if "Voice domain preference" in field.get('show'):
    #             for val in field.iter('field'):
    #                 if val.get('name') == 'gsm_a.gm.gmm.voice_domain_pref_for_eutran':
    #                     self.voice_domain_pref_for_eutran = val.get('show')

    def __callback_umts_nas(self, msg):
        """
        Extrace MM status and configurations from the NAS messages

        :param msg: the MM NAS message
        """

        for field in msg.data.iter('field'):

            if field.get('show') == "Quality Of Service - Negotiated QoS":
                field_val = {}

                # Default value setting
                field_val["gsm_a.gm.sm.qos.delay_cls"] = None
                field_val["gsm_a.gm.sm.qos.reliability_cls"] = None
                field_val["gsm_a.gm.sm.qos.peak_throughput"] = None
                field_val["gsm_a.gm.sm.qos.prec_class"] = None
                field_val["gsm_a.gm.sm.qos.mean_throughput"] = None
                field_val["gsm_a.gm.sm.qos.traffic_cls"] = None
                field_val["gsm_a.gm.sm.qos.del_order"] = None
                field_val["gsm_a.gm.sm.qos.max_bitrate_upl"] = None
                field_val["gsm_a.gm.sm.qos.max_bitrate_downl"] = None
                field_val["gsm_a.gm.sm.qos.ber"] = None
                field_val["gsm_a.gm.sm.qos.trans_delay"] = None
                field_val["gsm_a.gm.sm.qos.traff_hdl_pri"] = None
                field_val["gsm_a.gm.sm.qos.guar_bitrate_upl"] = None
                field_val["gsm_a.gm.sm.qos.guar_bitrate_downl"] = None
                field_val["gsm_a.gm.sm.qos.max_bitrate_downl_ext"] = None
                field_val["gsm_a.gm.sm.qos.guar_bitrate_downl_ext"] = None

                for val in field.iter('field'):
                    field_val[val.get('name')] = val.get('show')
                    if "Maximum SDU size" in val.get('show'):
                        field_val["gsm_a.gm.`sm.qos.max_sdu"] = val.get('value')

                # 10.5.6.5, TS24.008
                self.__mm_nas_status.qos_negotiated.delay_class = int(field_val['gsm_a.gm.sm.qos.delay_cls'])
                self.__mm_nas_status.qos_negotiated.reliability_class = int(field_val['gsm_a.gm.sm.qos.reliability_cls'])
                self.__mm_nas_status.qos_negotiated.peak_throughput = 1000 * pow(2, int(field_val["gsm_a.gm.sm.qos.peak_throughput"]) - 1)
                self.__mm_nas_status.qos_negotiated.precedence_class = int(field_val['gsm_a.gm.sm.qos.prec_class'])
                self.__mm_nas_status.qos_negotiated.mean_throughput = mean_tput[int(field_val["gsm_a.gm.sm.qos.mean_throughput"])]
                self.__mm_nas_status.qos_negotiated.traffic_class = int(field_val['gsm_a.gm.sm.qos.traffic_cls'])
                self.__mm_nas_status.qos_negotiated.delivery_order = int(field_val['gsm_a.gm.sm.qos.del_order'])
                self.__mm_nas_status.qos_negotiated.traffic_handling_priority = int(field_val['gsm_a.gm.sm.qos.traff_hdl_pri'])
                self.__mm_nas_status.qos_negotiated.residual_ber = residual_ber(int(field_val['gsm_a.gm.sm.qos.ber']))
                self.__mm_nas_status.qos_negotiated.transfer_delay = trans_delay(int(field_val['gsm_a.gm.sm.qos.trans_delay']))
                self.__mm_nas_status.qos_negotiated.max_bitrate_ulink = max_bitrate(int(field_val['gsm_a.gm.sm.qos.max_bitrate_upl']))
                self.__mm_nas_status.qos_negotiated.max_bitrate_dlink = max_bitrate(int(field_val['gsm_a.gm.sm.qos.max_bitrate_downl']))
                self.__mm_nas_status.qos_negotiated.guaranteed_bitrate_ulink = max_bitrate(int(field_val['gsm_a.gm.sm.qos.guar_bitrate_upl']))
                self.__mm_nas_status.qos_negotiated.guaranteed_bitrate_dlink = max_bitrate(int(field_val['gsm_a.gm.sm.qos.guar_bitrate_downl']))
                # self.__mm_nas_status.qos_negotiated.max_bitrate_ulink_ext = max_bitrate_ext(int(field_val['gsm_a.gm.sm.qos.max_bitrate_upl_ext']))
                self.__mm_nas_status.qos_negotiated.max_bitrate_dlink_ext = max_bitrate_ext(int(field_val['gsm_a.gm.sm.qos.max_bitrate_downl_ext']))
                # self.__mm_nas_status.qos_negotiated.guaranteed_bitrate_ulink_ext = max_bitrate_ext(int(field_val['gsm_a.gm.sm.qos.guar_bitrate_upl_ext']))
                self.__mm_nas_status.qos_negotiated.guaranteed_bitrate_dlink_ext = max_bitrate_ext(int(field_val['gsm_a.gm.sm.qos.guar_bitrate_downl_ext']))

    def __callback_esm(self, msg):
        """
        Extract ESM status and configurations from the NAS messages

        :param msg: the ESM NAS message
        """

        for field in msg.data.iter('field'):

            if field.get('show')=="Quality Of Service - Negotiated QoS": 

                field_val={}

                for val in field.iter('field'):
                    field_val[val.get('name')]=val.get('show')
                
                self.__esm_status.qos.delay_class=int(field_val['gsm_a.gm.sm.qos.delay_cls'])
                self.__esm_status.qos.reliability_class=int(field_val['gsm_a.gm.sm.qos.reliability_cls'])
                self.__esm_status.qos.precedence_class=int(field_val['gsm_a.gm.sm.qos.prec_class'])
                #10.5.6.5, TS24.008
                self.__esm_status.qos.peak_tput=1000*pow(2,int(field_val['gsm_a.gm.sm.qos.peak_throughput'])-1)
                self.__esm_status.qos.mean_tput=mean_tput[int(field_val['gsm_a.gm.sm.qos.mean_throughput'])]
                self.__esm_status.qos.traffic_class=int(field_val['gsm_a.gm.sm.qos.traffic_cls'])
                self.__esm_status.qos.delivery_order=int(field_val['gsm_a.gm.sm.qos.del_order'])
                self.__esm_status.qos.traffic_handling_priority=int(field_val['gsm_a.gm.sm.qos.traff_hdl_pri'])
                self.__esm_status.qos.residual_ber=residual_ber[int(field_val['gsm_a.gm.sm.qos.ber'])]

                self.__esm_status.qos.transfer_delay=trans_delay(int(field_val['gsm_a.gm.sm.qos.trans_delay']))

                self.__esm_status.qos.max_bitrate_ulink=max_bitrate(int(field_val['gsm_a.gm.sm.qos.max_bitrate_upl']))
                self.__esm_status.qos.max_bitrate_dlink=max_bitrate(int(field_val['gsm_a.gm.sm.qos.max_bitrate_downl']))
                self.__esm_status.qos.guaranteed_bitrate_ulink=max_bitrate(int(field_val['gsm_a.gm.sm.qos.guar_bitrate_upl']))
                self.__esm_status.qos.guaranteed_bitrate_dlink=max_bitrate(int(field_val['gsm_a.gm.sm.qos.guar_bitrate_downl']))
                
                self.__esm_status.qos.max_bitrate_ulink_ext=max_bitrate_ext(int(field_val['gsm_a.gm.sm.qos.max_bitrate_upl_ext']))
                self.__esm_status.qos.max_bitrate_dlink_ext=max_bitrate_ext(int(field_val['gsm_a.gm.sm.qos.max_bitrate_downl_ext']))
                self.__esm_status.qos.guaranteed_bitrate_ulink_ext=max_bitrate_ext(int(field_val['gsm_a.gm.sm.qos.guar_bitrate_upl_ext']))
                self.__esm_status.qos.guaranteed_bitrate_dlink_ext=max_bitrate_ext(int(field_val['gsm_a.gm.sm.qos.guar_bitrate_downl_ext']))

                self.logger.info(self.__esm_status.qos.dump_rate())
                self.logger.info(self.__esm_status.qos.dump_delivery())
                # self.__esm_status.qos.dump_rate()
                # self.__esm_status.qos.dump_delay()

    def __rrc_filter(self, msg):
        """
        Filter all LTE RRC packets, and call functions to process it

        :param msg: the event (message) from the trace collector.
        """
        log_item = msg.data.decode()
        log_item_dict = dict(log_item)

        #Convert msg to dictionary format
        raw_msg = Event(msg.timestamp, msg.type_id, log_item_dict)

        # store current carrier info, e.g. 310260 (mcc_mnc)
        # self.__callback_serv_cell(raw_msg)

        if 'Msg' not in log_item_dict:
            return
        
        # Calllbacks triggering
        if msg.type_id == "LTE_RRC_OTA_Packet":   

            #Convert msg to xml format
            log_xml = ET.XML(log_item_dict['Msg'])
            xml_msg = Event(msg.timestamp, msg.type_id, log_xml)

            # detect network accessibility
            self.__is_network_unavailable(xml_msg)

            # detect neighbor cell id (RAT type) and signal strength
            # self.__get_meas_report(xml_msg)

            # Raise event to other analyzers
            # e = Event(timeit.default_timer(),self.__class__.__name__,"")
            # self.send(e)
            self.send(xml_msg) # deliver LTE RRC signaling messages (decoded)

    def __callback_serv_cell(self, msg):

        """
        A callback to update current cell status

        :param msg: the RRC messages with cell status
        """
        # Sample:
        # <dm_log_packet><pair key="type_id">LTE_RRC_Serv_Cell_Info_Log_Packet</pair><pair key="timestamp">2015-11-15 01:53:07.204390</pair><pair key="Version">3</pair><pair key="Physical Cell ID">328</pair><pair key="DL FREQ">2300</pair><pair key="UL FREQ">20300</pair><pair key="DL BW">20 MHz</pair><pair key="UL BW">20 MHz</pair><pair key="Cell Identity">22205186</pair><pair key="TAC">16340</pair><pair key="Band Indicator">4</pair><pair key="MCC">310</pair><pair key="MNC Digit">3</pair><pair key="MNC">260</pair><pair key="Allowed Access">0</pair></dm_log_packet>
        status_updated = False
        if not self.__status.inited():
            if 'Freq' in msg.data:
                status_updated = True
                self.__status.freq = msg.data['Freq']
            if 'Physical Cell ID' in msg.data:
                status_updated = True
                self.__status.id = msg.data['Physical Cell ID']
            if 'TAC' in msg.data:
                status_updated = True
                self.__status.tac = msg.data['TAC']
            if 'MCC' in msg.data:
                status_updated = True
                self.__status.mcc = msg.data['MCC']
            if 'MNC' in msg.data:
                status_updated = True
                self.__status.mnc = msg.data['MNC']
        else:
            if 'Freq' in msg.data and self.__status.freq != msg.data['Freq']:
                status_updated = True
                curr_conn = self.__status.conn
                self.__status = LteRrcStatus()
                self.__status.conn = curr_conn
                self.__status.freq = msg.data['Freq']
                # self.__history[msg.timestamp] = self.__status
            if 'Physical Cell ID' in msg.data and self.__status.id != msg.data['Physical Cell ID']:
                status_updated = True
                curr_conn = self.__status.conn
                self.__status = LteRrcStatus()
                self.__status.conn = curr_conn
                self.__status.id = msg.data['Physical Cell ID']
                # self.__history[msg.timestamp] = self.__status
            if 'TAC' in msg.data and self.__status.id != msg.data['TAC']:
                status_updated = True
                curr_conn = self.__status.conn
                self.__status = LteRrcStatus()
                self.__status.conn = curr_conn
                self.__status.tac = msg.data['TAC']
                # self.__history[msg.timestamp] = self.__status
            if 'MCC' in msg.data and self.__status.mcc != msg.data['MCC']:
                status_updated = True
                curr_conn = self.__status.conn
                self.__status = LteRrcStatus()
                self.__status.conn = curr_conn
                self.__status.mcc = msg.data['MCC']
                # self.__history[msg.timestamp] = self.__status
            if 'MNC' in msg.data and self.__status.mcc != msg.data['MNC']:
                status_updated = True
                curr_conn = self.__status.conn
                self.__status = LteRrcStatus()
                self.__status.conn = curr_conn
                self.__status.mbc = msg.data['MNC']
                # self.__history[msg.timestamp] = self.__status
        
        if status_updated:
            # self.logger.info(self.__status.dump())
            self.__status.mcc_mnc = str(self.__status.mcc + self.__status.mnc)
            # pass

    def __get_meas_report(self, msg):
        """
        get the signal strength measurement report to prevent fault decision

        """
        # Sample

        # <field name="lte-rrc.measIdToAddModList" pos="57" show="2" showname="measIdToAddModList: 2 items" size="4" value="20000200">
        #   <field name="" pos="57" show="Item 0" size="2" value="2000">
        #     <field name="lte-rrc.MeasIdToAddMod_element" pos="57" show="" showname="MeasIdToAddMod" size="2" value="">
        #       <field name="lte-rrc.measId" pos="57" show="1" showname="measId: 1" size="1" value="20" />
        #       <field name="lte-rrc.measObjectId" pos="58" show="1" showname="measObjectId: 1" size="1" value="00" />
        #       <field name="lte-rrc.reportConfigId" pos="58" show="1" showname="reportConfigId: 1" size="1" value="00" />
        #     </field>
        #   </field>
        #   <field name="" pos="59" show="Item 1" size="2" value="0200">
        #     <field name="lte-rrc.MeasIdToAddMod_element" pos="59" show="" showname="MeasIdToAddMod" size="2" value="">
        #       <field name="lte-rrc.measId" pos="59" show="2" showname="measId: 2" size="1" value="02" />
        #       <field name="lte-rrc.measObjectId" pos="59" show="1" showname="measObjectId: 1" size="1" value="02" />
        #       <field name="lte-rrc.reportConfigId" pos="60" show="2" showname="reportConfigId: 2" size="1" value="00" />
        #     </field>
        #   </field>
        # </field>


        # 12/05 Change to the optional solution -- check the return list of the bplmn search

        # if field.get('name') == "lte-rrc.c1":
        #     for val in field.iter('field'):
        #         if field.get('name') == "lte-rrc.measResultPCell_element":
        #             for val in field.iter('field'):
        #                 if val.get('name') == "lte-rrc.rsrpResult":
        #                     self.current_cell_rsrp = val.get('show') - 140 # 4G cell

        #         # TODO: did not finished here
        #         if field.get('name') == "lte-rrc.measResultNeighCells":
        #             for val in field.iter('field'):
        #                 if val.get('name') == "lte-rrc.MeasResultEUTRA_element":
        #                     name="lte-rrc.physCellId"
        #                 if val.get('name') == "lte-rrc.rsrpResult":
        #                     self.current_cell_rsrp = val.get('show') - 140 # 4G cell

    def __is_network_unavailable(self, msg):
        """
        The background monitor detects whether the current scanned result is an unavailable network or not
        """
        for field in msg.data.iter('field'):

            # case I (Forbidden access) -- find in RRC SIB, indicated by access_baring_option == True
            # for LTE RRC message
            # retrieve ac-Barring info in the sib2
            if field.get('name') == "lte-rrc.sib2_element":
                for val in field.iter('field'):
                    if "ac-BarringInfo" in val.get('show') and val.get('value') == "0":
                        # send a signal to discard this search result
                        # but how do I know the current carrier being searched?
                        self.current_network_inaccessible = True
                        break

            # case II (Switch to carriers with incomplete service) -- find in TAU, to see if it is CS-only or CS-preferred
            # for LTE NAS message
            if "Voice domain preference" in field.get('show'):
                for val in field.iter('field'):
                    if val.get('name') == 'gsm_a.gm.gmm.voice_domain_pref_for_eutran' and (("CS Voice only" or "prefer CS Voice") in val.get('show')):
                        self.voice_domain_pref_for_eutran = True
                        break
                # if False#some condition (maybe CS Voice only) that will made the CSFB fail:
                #     self.current_network_inaccessible = True

            # case III
            # TODO - need support of measurement report
            # if field.get('name') == "lte-rrc.sib3_element":

    def __voice_preferred_csfb(self, msg):
        """
        The background monitor detects whether required CSFB is CS only or CS preferred
        """
        # case II (Switch to carriers with incomplete service) -- find in TAU, to see if it is CS-only or CS-preferred
        # for LTE NAS message
        for field in msg.data.iter('field'):
            if "Voice domain preference" in field.get('show'):
                for val in field.iter('field'):
                    if val.get('name') == 'gsm_a.gm.gmm.voice_domain_pref_for_eutran' and (("CS Voice only" or "prefer CS Voice") in val.get('show')):
                        self.voice_domain_pref_for_eutran = True
                        break
                # if False#some condition (maybe CS Voice only) that will made the CSFB fail:
                #     self.current_network_inaccessible = True

    def parse_bplmn_res(self, at_res):

        '''
            Parse the returned bplmn results. Save to bplmn database

            :param at_res: raw results from AT command
        ''' 

        # lock database in update
        self.lock.acquire()

        # Reset data base
        # self.bplmn_database = {}
        # self.last_update_time = -1

        self.wcdma_available = False

        self.last_update_time = time.time()

        token1 = '+COPS: '
        token2 = 'OK'
        index1 = at_res.find(token1)
        index2 = at_res.find(token2)
        tmp = at_res[index1 + len(token1):index2]

        while True:
            index3 = tmp.find('(')
            index4 = tmp.find(')')
            if index3 == -1 or index4 == -1:
                break

            item = tmp[index3 + 1:index4].split(',')

            if len(item) >= 5:
                # after update, if this item's last_update_time != self.last_update_time, it is outdated
                if item[0] == 2 or item[0] == 0: # scanned cell type is NETWORK_MODE_WCDMA_PREF = 0 or NETWORK_MODE_WCDMA_ONLY = 2
                    self.wcdma_available = True

                # case II -- check CSFB
                # needs CS Voice CSFB, but currently no wcdma cell available
                if self.voice_domain_pref_for_eutran == True and self.wcdma_available == False:
                    continue
                else:
                    self.bplmn_database[item[1][1:-1]] = BplmnItem(item[0],item[1][1:-1],item[3],item[4],self.last_update_time)
                    print time.time(),"BPLMN-search",item[0],item[1][1:-1],item[3],item[4],self.last_update_time
            
            tmp = tmp[index4+2:]

        # if len(self.bplmn_database)>0:
        #     self.last_update_time = time.time()

        # print "BPLMN done",self.last_update_time,len(self.bplmn_database)

        self.lock.release()

    def run_once(self):
        '''
            API for calling BPLMN search (run only once)
        '''
        print "BPLMN searching..."
        at_res = self.at_cmd.run_cmd("AT+COPS=?")

        # only parse the current result if the network access is not barred
        if (self.current_network_inaccessible == False):
            self.parse_bplmn_res(at_res)

    def run(self):

        '''
            Repetitive perform bplmn search
            NOTE: this function runs in an infinite loop. 
            To avoid blocking, please run it as a separate thread
        '''
        #TODO: to save power, run it with a configurable timer
        while True:
            self.run_once()   


if __name__ == "__main__":

    '''
    Sample output:
    11-28 16:51:20.222 1448758280.22 BPLMN-search 2 Project Fi "310260" 7 1448758280.22
    11-28 16:51:20.223 1448758280.22 BPLMN-search 1 Project Fi "310260" 2 1448758280.22
    11-28 16:51:20.224 1448758280.22 BPLMN-search 1 Project Fi "310260" 0 1448758280.22
    11-28 16:51:20.225 1448758280.22 BPLMN-search 1 Project Fi "311480" 7 1448758280.22
    11-28 16:51:20.225 1448758280.23 BPLMN-search 1 Project Fi "310410" 7 1448758280.22
    11-28 16:51:20.226 1448758280.23 BPLMN-search 1 Project Fi "310410" 2 1448758280.22
    11-28 16:51:20.227 1448758280.23 BPLMN-search 1 Project Fi "310410" 0 1448758280.22
    11-28 16:51:20.228 1448758280.23 BPLMN-search 0  3 4 1448758280.22
    11-28 16:51:21.390 BPLMN searching...
    11-28 16:51:22.867 BPLMN searching...

    '''
    # bplmn_search = BplmnSearch("/dev/smd11")
    bplmn_search = BplmnSearch(at_serial_port)
    bplmn_search.run()