#!/usr/bin/python
# Filename: icellular_sample_collection.py
"""
iCellular inter-carrier selection engine

It loads the decision strategy and performs inter-carrier selection. 
NOTE: this module is NOT decision strategy itself

Author: Yuanjie Li
"""


from mobile_insight.analyzer import Analyzer

import config


class IcellularSampleCollection(Analyzer):

    def __init__(self):
        '''
        Initialize the decision engine
        '''

        Analyzer.__init__(self)

        self.prediction_metric_type = config.prediction_metric_type
        self.__prediction_metric = None
        self.__import_prediction_metric()

        self.add_source_callback(self.__collect_sample)

    def set_source(self,source):
        """
        Set the trace source. Enable the LTE RRC messages.

        :param source: the trace source.
        :type source: trace collector
        """
        Analyzer.set_source(self,source)


    def __import_prediction_metric(self):
        '''
        Import the module of decision strategy specified by self.decision_strategy
        '''
        try:
            module_tmp = __import__("sample_collection")
            analyzer_tmp = getattr(module_tmp,self.prediction_metric_type)
            self.__prediction_metric = analyzer_tmp()
        except Exception, e:
            print "iCellular: no sample prediction metric "+self.decision_strategy
            import traceback
            import sys
            sys.exit(str(traceback.format_exc()))    

    def __collect_sample(self,msg):
        '''
        Try to get samples in response to each cellular log

        :param msg: not used
        '''
        res = self.__prediction_metric.collect()
        if res:
            self.send(res)

