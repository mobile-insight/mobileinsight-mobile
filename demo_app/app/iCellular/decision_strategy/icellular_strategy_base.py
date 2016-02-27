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
        # best_lantency = 1e10
        # best_carrier = None
        # for carrier, data in carrier_network_list.items():
        #     result = predict(self.fit, [y for x, y in data.items()])
        #     if result < best_lantency:
        #         best_lantency = result
        #         best_carrier = carrier
        # return best_carrier

        return None

if __name__ == '__main__':
    test = {'att': {'1': 2,'2':-100.8,'3':0,'4': 90},'tmobile':{'1':2, '2':-109.6,'3':0, '4': 99.5 }}
    print IcellularStrategyBase().selection(test)
