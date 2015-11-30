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

class BplmnSearch:

    def __init__(self, at_serial_port):

        '''
            Initialize the search daemon

            :param at_serial_port: the serial port that can be used to send AT command 
        '''

        self.at_cmd = AtCmd(at_serial_port)
        self.bplmn_database = {}  # Carrier -> Availability
        self.last_update_time = -1 # last time to update bplmn result. -1 means not available
        self.lock = thread.allocate_lock() # a lock between monitor and decision


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

        # Zengwen's commment:
        # what are these lines doing? regex search??
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