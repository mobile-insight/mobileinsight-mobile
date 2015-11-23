#!/usr/bin/python
# Filename: decision_strategy.py

"""
An abstract decision strategy layer for inter-carrier switch

Author: Yuanjie Li
"""

class DecisionStrategy:

    #Network type constants
    NETWORK_MODE_WCDMA_PREF = 0
    NETWORK_MODE_GSM_ONLY = 1
    NETWORK_MODE_WCDMA_ONLY = 2
    NETWORK_MODE_GSM_AUTO = 3
    NETWORK_MODE_CDMA_AUTO = 4
    NETWORK_MODE_CDMA_NO_EVDO = 5
    NETWORK_MODE_EVDO_NO_CDMA = 6
    NETWORK_MODE_GSM_CDMA_AUTO = 7
    NETWORK_MODE_LTE_CDMA_AUTO = 8
    NETWORK_MODE_LTE_GSM_AUTO = 9
    NETWORK_MODE_LTE_GSM_CDMA_AUTO = 10
    NETWORK_MODE_LTE_ONLY = 11
    
    def __init__(self,monitor):
        """
            Initialize the decision layer with a monitor

            :param monitor: the monitor to be used to get decision information
        """
        self.monitor = monitor

    def make_decision(self):
        """
            Keep querying monitor and make decisions

            :returns : a (carrier, network_type) pair
        """    
        return ("Auto",self.NETWORK_MODE_LTE_GSM_CDMA_AUTO)

        


