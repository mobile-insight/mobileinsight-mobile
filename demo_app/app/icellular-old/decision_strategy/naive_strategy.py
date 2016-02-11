#!/usr/bin/python
# Filename: naive_strategy.py

"""
A naive strategy for selecting the target carrier and network type

Author: Yuanjie Li
"""

from decision_strategy import *

class NaiveStrategy(DecisionStrategy):
    
    def __init__(self,monitor):
        """
            Initialize the decision layer
        """
        DecisionStrategy.__init__(self,monitor)


    
    def make_decision(self):
        """
            Make the switch decision. 
            For naive strategy, always return the auto selection mode (default in Project-Fi)

            :returns : a (carrier, network_type) pair
        """    
        return ("Auto",self.NETWORK_MODE_LTE_GSM_CDMA_AUTO)

