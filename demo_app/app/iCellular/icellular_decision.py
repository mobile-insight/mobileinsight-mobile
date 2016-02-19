#!/usr/bin/python
# Filename: icellular_decision.py
"""
iCellular inter-carrier selection engine

It loads the decision strategy and performs inter-carrier selection. 
NOTE: this module is NOT decision strategy itself

Author: Yuanjie Li
"""


from mobile_insight.analyzer import Analyzer


class IcellularDecision(Analyzer):

    def __init__(self, decision_strategy="TestStrategy"):
        '''
        Initialize the decision engine

        :param decision_strategy: the name of the decision strategy (located in app/decision_strategy)
        :type monitor_list: string
        '''

        Analyzer.__init__(self)

        self.decision_strategy = decision_strategy
        self.__decision_module = None
        self.__import_decision_strategy()

        self.include_analyzer("IcellularMonitor",[self.__selection_decision])

    def set_source(self,source):
        """
        Set the trace source. Enable the LTE RRC messages.

        :param source: the trace source.
        :type source: trace collector
        """
        Analyzer.set_source(self,source)


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
        res = self.__decision_module.selection(msg)
        if res:
            #Inter-carrier switch is needed. Send an event to switch engine
            self.send(res)

