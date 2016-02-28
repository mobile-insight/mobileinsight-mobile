#!/usr/bin/python
# Filename: opensignal_latency.py
"""
Base class of prediction sample collection

Author: Yuanjie Li
"""


from sample_collection_base import SampleCollectionBase 

class OpensignalLatency(SampleCollectionBase):

    def __init__(self):
        pass

    def collect(self):
        """
        Collect one prediction metric by calling specific APIs
        """
        return None
