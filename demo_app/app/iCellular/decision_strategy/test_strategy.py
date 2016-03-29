#!/usr/bin/python
# Filename: test_strategy.py
"""
A test strategy for basic functions

Author: Yuanjie Li
"""

from icellular_strategy_base import IcellularStrategyBase


class TestStrategy(IcellularStrategyBase):
    
    def __init__(self):
        IcellularStrategyBase.__init__(self)

    def selection(self, carrier_network_list):
        return None 

    def training(self,sample):
    	"""
    	Online training sample collection and training. 

    	Currently this function is for regression tree algorithm only

    	:param sample: a sample from serving carrier network
    	:type sample: a tuple of (x,y), where x is the feature vector (dictionary), and y is the prediction metric
    	"""
    	print "TestStrategy: "+str(sample.x)+" "+str(sample.y)