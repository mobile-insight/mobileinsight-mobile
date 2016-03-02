#!/usr/bin/python
# Filename: icellular_decision.py
"""
iCellular inter-carrier selection engine

It loads the decision strategy and performs inter-carrier selection. 
NOTE: this module is NOT decision strategy itself

Author: Yuanjie Li
"""


from mobile_insight.analyzer import Analyzer
from mobile_insight.element import Event

import config

class Sample:
    def __init__(self,x,y):
        self.x = x
        self.y = y


class IcellularDecision(Analyzer):

    # def __init__(self, decision_strategy="TestStrategy"):
    def __init__(self):
        '''
        Initialize the decision engine
        '''

        Analyzer.__init__(self)

        self.decision_strategy = config.decision_strategy
        self.__decision_module = None
        self.__import_decision_strategy()

        self.include_analyzer("IcellularMonitor",[self.__selection_decision])
        self.include_analyzer("IcellularSampleCollection",[self.__create_sample])
        self.include_analyzer("LteNasAnalyzer",[self.__update_cur_feature_vector])
        # self.include_analyzer("UmtsNasAnalyzer",[self.__update_cur_feature_vector])

        self.__cur_feature_vector = {}
        self.__cur_signal_strength = None #Yuanjie: a temporarily impl for signal strength

    def set_source(self,source):
        """
        Set the trace source. Enable the LTE RRC messages.

        :param source: the trace source.
        :type source: trace collector
        """
        Analyzer.set_source(self,source)


    def __update_cur_feature_vector(self,msg):
        """
        Update current vector feature
        """

        if msg.type_id == "LTE_NAS_ESM_Plain_OTA_Incoming_Message" \
        or msg.type_id == "LTE_NAS_ESM_Plain_OTA_Outgoing_Message":
            # LTE NAS: get QoS
            qos_profile = self.get_analyzer("LteNasAnalyzer").get_qos()

            if not self.__cur_signal_strength \
            or not qos_profile.delay_class \
            or not qos_profile.qci:
                return

            self.__cur_feature_vector['signal_strength'] = self.__cur_signal_strength
            self.__cur_feature_vector['delay_class']=qos_profile.delay_class
            self.__cur_feature_vector['qci']=qos_profile.qci
            # self.__cur_feature_vector['max_bitrate_dlink']=qos_profile.max_bitrate_dlink
            # self.__cur_feature_vector['guaranteed_bitrate_dlink']=qos_profile.guaranteed_bitrate_dlink


    def __import_decision_strategy(self):
        '''
        Import the module of decision strategy specified by self.decision_strategy
        '''
        try:
            module_tmp = __import__("decision_strategy")
            analyzer_tmp = getattr(module_tmp,self.decision_strategy)
            self.__decision_module = analyzer_tmp()
        except Exception, e:
            print "iCellular: no decision strategy "+self.decision_strategy
            import traceback
            import sys
            sys.exit(str(traceback.format_exc()))    

    def __selection_decision(self,msg):
        '''
        Perform inter-carrier selection decision

        :param msg: this is a list of available carrier networks and their runtime measurements
        '''
        # print "__selection_decision: "+str(msg)

        if msg.type_id == "iCellular_selection":
            res = self.__decision_module.selection(msg.data)
            if res:
                #Inter-carrier switch is needed. Send an event to switch engine
                self.send(res)
        elif msg.type_id == "iCellular_serv_rss":
            self.__cur_signal_strength = msg.data

    def __create_sample(self,metric):
        '''
        Create a new training sample

        :param msg: a new prediction metric
        '''
        if not self.__cur_feature_vector:
            return
        print "sample: ("+str(self.__cur_feature_vector)+","+str(metric)+")"
        sample = Sample(metric,self.__cur_feature_vector)
        res = self.__decision_module.training(sample)

