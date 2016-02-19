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