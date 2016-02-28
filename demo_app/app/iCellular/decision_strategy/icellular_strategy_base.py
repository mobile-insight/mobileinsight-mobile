#!/usr/bin/python
# Filename: icellular_strategy_base.py
"""
Base class of decisions strategies.
This defines the common interface for selection decision.

Author: Yuanjie Li
"""

class IcellularStrategyBase(object):

    def __init__(self):
        pass

    def selection(self, carrier_network_list):
        """
        Select the target carrier network given the available candidate dict

        :param carrier_network_list: a dict of available carriers
        :returns: the target carrier network, or None if no switch is needed
        """
        return None


    def training(self,sample):
    	"""
    	Online training sample collection and training. 

    	Currently this function is for regression tree algorithm only

    	:param sample: a sample from serving carrier network
    	:type sample: a tuple of (x,y), where x is the feature vector (dictionary), and y is the prediction metric
    	"""
    	pass
