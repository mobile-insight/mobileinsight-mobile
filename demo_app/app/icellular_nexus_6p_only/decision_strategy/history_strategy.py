#!/usr/bin/python
# Filename: history_strategy.py

"""
A history-based decision strategy.
It requires a profile of <location,time,carrier,network_type>, 
which is learned offline from the users' daily usage logs

Author: Yuanjie Li
"""

from decision_strategy import *
import datetime
from math import radians, cos, sin, asin, sqrt

class HistoryProfile:
    
    """
        A decision profile item
    """
    def __init__(self,profile_time,latitude,longitude,pref_list):
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.pref_list = pref_list

        #Convert time to seconds (float)
        tmp = profile_time.split(":")
        if len(tmp)==3:
            self.time = float(tmp[0])*3600+float(tmp[1])*60+float(tmp[2])
        else:
            self.time = -1

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
        f = open(self.history_profile)
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
                tmp_split=tmp[i].split(',')
            	tmp_list.append((tmp_split[0],int(tmp_split[1])))

            profile_item = HistoryProfile(tmp[0],tmp[1],tmp[2],tmp_list)

            self.profile.append(profile_item)


    def _gps_distance(self,lat1,lon1, lat2, lon2):
        """
            Calculate the great circle distance between two points 
            on the earth (specified in decimal degrees)

            :returns: the distance in km
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles
        # print "distance",c*r
        return c * r

    def _time_difference(self,item,current_time):
        if item.time==-1:
            return -1
        else:
            tmp = current_time.hour*3600+current_time.minute*60+current_time.second+current_time.microsecond/1000000
            return abs(tmp-item.time)


    def _search_closest_location(self,gps_location):
        """
            Return profiles closest to the target lcoation

            :param gps_location: current gps location
            :returns: a list of profiles closest to the current gps location
        """

        min_distance = float("inf")
        res = []
        for item in self.profile:
            # distance = self._gps_distance(item.longitude,gps_location[1],item.latitude,gps_location[0])
            distance = self._gps_distance(gps_location[0],gps_location[1],item.latitude,item.longitude)
            if distance < min_distance:
                res = [item]
                min_distance = distance
            elif distance ==  min_distance:
                res.append(item)
        return res


    def _search_closest_time(self,candidate1,current_time):
        """
            Return profiles closest to the current time

            :param candidate1: result from _search_closest_location
            :param current_time: current time

            :returns: a list of profiles closest to the current gps location
        """
        min_time = float("inf")
        res = []
        for item in candidate1:
            time_diff = self._time_difference(item,current_time)
            if time_diff==-1:
                continue
            if time_diff<min_time:
                res = [item]
                min_time = time_diff
            elif time_diff==min_time:
                res.append(item)

        return res
                



    def make_decision(self):
        """
            Make a inter-carrier switch decision based on history profile
            The decision logic is as follows:
                (1) Query the device's current location and time
                (2) Search the history profile, find the profiles with closest location
                (3) Among the profile items in (2), find the profile with closest time
                (4) For (3), based on the preference list, switch to the first (carrier,network) 
                that is available based on BPLMN results

            In addition, some thresholds may be set, s.t. if (2) and (3) do not offer satisfying profile,
            set the device into auto selection mode (default in Project-Fi)

            :returns : a (carrier, network_type) pair
        """    

        # (1) Query the device's current location and time
        gps_location = self.monitor.get_current_location()
        current_time = datetime.datetime.now()

        # (2) Search the history profile, find the profiles with closest location
        candidate1 = self._search_closest_location(gps_location)
        # print candidate1

        # (3) Among the profile items in (2), find the profile with closest time
        candidate2 = self._search_closest_time(candidate1,current_time)
        # print candidate2

        # (4) Based on the pref list, choose the first available (carrier,network_type) 
        # to switch based on BPLMN results
        profile_item = candidate2[0]

        # target = ("Auto",self.NETWORK_MODE_LTE_GSM_CDMA_AUTO)
        target = None

        # self.monitor.bplmn.lock.acquire()
        if self.monitor.bplmn.last_update_time != -1:
            # Only make decision when the BPLMN result is available
            for item in profile_item.pref_list:
                # if item[0] in self.monitor.bplmn.bplmn_database \
                # and self.monitor.bplmn.bplmn_database[item[0]].mode != 3: #avoid switching to forbidden RAT
                if item[0] in self.monitor.bplmn.bplmn_database \
                and self.monitor.bplmn.bplmn_database[item[0]].last_update_time == self.monitor.bplmn.last_update_time: 
                    #Carrier is available
                    target = item
                    break 

        # self.monitor.bplmn.lock.release()    

        print self.__class__.__name__,target

        return target
        