#!/usr/bin/python
# Filename: history_strategy.py

"""
A history-based decision strategy.
It requires a profile of <location,time,carrier,network_type>, 
which is learned offline from the users' daily usage logs

Author: Yuanjie Li
"""

class HistoryProfile:
    
    """
        A decision profile item
    """
    def __init__(self,time,latitude,longitude,pref_list):
        self.time = time
        self.latitude = latitude
        self.longitude = longitude
        self.pref_list = pref_list

class HistoryStrategy(DecisionStrategy):

    def __init__(self,monitor,history_profile):
        """
            Initialize the decision layer

            :param monitor: the monitor to be used (report GPS location and time)
            :param history_profile: a file that contains learned <location,time,carrier,network_type>
        """
        DecisionStrategy.__init__(self,monitor)
        self.history_profile = history_profile
        self.profile = []
        self._read_profile()


    def _read_profile(self):
        """
            Read history profiles from the file
        """
        f = open(history_profile)
        while True:
            line = f.readline()
            if not line:
                break

            if line[0]=="#": #comment
                continue

            tmp = line.split(' ') #invalid profile
            if len(tmp)<4:
                continue

            tmp_list = []
            for i in range(3,len(tmp)):
            	tmp_list.append(tmp[i])

            profile_item = HistoryProfile(tmp[0],tmp[1],tmp[2],tmp_list)

            self.profile.append(profile_item)

    def make_decision(self):
        """
            Keep querying monitor and make decisions


            :returns : a (carrier, network_type) pair
        """    
        return ("Sprint",self.NETWORK_MODE_LTE_ONLY)