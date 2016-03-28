#!/usr/bin/python
# Filename: radio_link_capacity.py
"""
Collect radio link capacity

Author: Yuanjie Li
"""


from sample_collection_base import SampleCollectionBase 

class RadioLinkCapacity(SampleCollectionBase):

    def __init__(self):
        SampleCollectionBase.__init__(self)

    def log_needed(self):
    	"""
    	Report the MobileInsight logs it needed to get the metrics
    	Currently used by LTE link capacity only

    	:returns: a list of logs to be enabled
    	"""
    	return "LTE_PHY_PDSCH_Packet"

    def collect(self,msg):
        """
        Collect one prediction metric by calling specific APIs

        :param msg: a MobileInsight message
        :type msg: Event
        :returns: the runtime radio link capacity (in bps)
        """
        if msg.type_id=="LTE_PHY_PDSCH_Packet":
            log_item = msg.data.decode()
            print "RadioLinkCapacity: "+str(log_item["Transport Block Size Stream 0"])
            log_item = msg.data.decode()
            return str(log_item["Transport Block Size Stream 0"])
