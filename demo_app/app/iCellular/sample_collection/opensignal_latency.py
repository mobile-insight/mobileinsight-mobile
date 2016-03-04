#!/usr/bin/python
# Filename: opensignal_latency.py
"""
Base class of prediction sample collection

Author: Yuanjie Li
"""


from sample_collection_base import SampleCollectionBase 

class OpensignalLatency(SampleCollectionBase):

    def __init__(self):
        SampleCollectionBase.__init__(self)

    def log_needed(self):
    	"""
    	Report the MobileInsight logs it needed to get the metrics
    	Currently used by LTE link capacity only

    	:returns: a list of logs to be enabled
    	"""
    	return None

    def collect(self,msg):
        """
        Collect one prediction metric by calling specific APIs
        """
        return None
