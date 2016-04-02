#!/usr/bin/python
# Filename: sample_collection_base.py
"""
Base class of prediction sample collection

Author: Yuanjie Li
"""


class SampleCollectionBase(object):

    def __init__(self):
        pass

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

        :param msg: the raw message from MobileInsight monitor
        :type msg: Event
        """
        return None
