#!/usr/bin/python
# Filename: bplmn-search.py

"""
A background PLMN search module. Help reduce unavailability PLMN search overhead

Author: Yuanjie Li
"""

import time
import thread
import threading

from at_cmd import * 


try: 
    import xml.etree.cElementTree as ET 
except ImportError: 
    import xml.etree.ElementTree as ET
from analyzer import *
from protocol_analyzer import *
import timeit
import time

from profile import Profile, ProfileHierarchy

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

class BplmnSearch(ProtocolAnalyzer):

    def __init__(self, at_serial_port):

        '''
            Initialize the search daemon

            :param at_serial_port: the serial port that can be used to send AT command 
        '''

        self.current_network_inaccessible = False

        ProtocolAnalyzer.__init__(self)
        self.add_source_callback(self.__rrc_filter)

        self.at_cmd = AtCmd(at_serial_port)

        #init internal states
        self.__status = LteRrcStatus()    # current cell status

        self.bplmn_database = {}  # Carrier -> Availability
        self.last_update_time = -1 # last time to update bplmn result. -1 means not available
        self.lock = thread.allocate_lock() # a lock between monitor and decision

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

    def __is_network_unavailable(self, msg):
        """
        The background monitor detects the current scanned result is an unavailable network
        """
        for field in msg.data.iter('field'):

            # retrieve ac-Barring info in the sib2
            if field.get('name') == "lte-rrc.sib2_element":
                for val in field.iter('field'):
                    if "ac-BarringInfo" in val.get('show') and val.get('value') == "0":
                        # send a signal to discard this search result
                        # but how do I know the current carrier being searched?
                        self.current_network_inaccessible = True

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
        if (!self.current_network_inaccessible):
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