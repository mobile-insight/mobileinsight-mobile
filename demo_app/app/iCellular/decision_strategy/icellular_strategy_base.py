#!/usr/bin/python
# Filename: icellular_strategy_base.py
"""
Base class of decisions strategies.
This defines the common interface for selection decision.

Author: Yuanjie Li
"""
# from cart_interface import getTree, predict

class IcellularStrategyBase(object):

    def __init__(self):
        # self.fit = getTree()
        pass

    def selection(self, carrier_network_list):
        """
        Select the target carrier network given the available candidate dict

        :param carrier_network_list: a dict of available carriers
        :returns: the target carrier network, or None if no switch is needed
        """
