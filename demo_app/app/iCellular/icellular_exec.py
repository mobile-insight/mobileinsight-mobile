#!/usr/bin/python
# Filename: icellular_exec.py
"""
iCellular direct switch

It achieves direct switch and reduces the service interruption time.

Author: Yuanjie Li
"""


from at_cmd import * 
import config

from mobile_insight.analyzer import Analyzer

class IcellularExec(Analyzer):

    # def __init__(self, at_serial_port="/dev/smd11"):
    def __init__(self):

        '''
        Initialization

        :at_serial_port: in-phone device that connects to AT command at_serial_port
        :type at_serial_port: string
        '''

        #No MobileInsight monitor callback, but it relies on command from decision strategy
        Analyzer.__init__(self)
        self.include_analyzer("IcellularDecision",[self.__run_switch])

        #FIXME: conflicts with AtCmd in IcellularMonitor
        self.__at_cmd = AtCmd(config.at_serial_port)  # AT command port

    def set_source(self,source):
        """
        Set the trace source. Enable the LTE RRC messages.

        :param source: the trace source.
        :type source: trace collector
        """
        Analyzer.set_source(self,source)

    def __run_secret_code(self,code):
        """
        Dial a secret code in Android

        :param code: the secret code to dail
        """

        self.run_shell_cmd("am broadcast -a \"android.provider.Telephony.SECRET_CODE\" -d \"android_secret_code://" + code + "\"")


    def __get_network_type(self):
        """
        Return a current network type
        """
        #Nexus 6P only: setPreferredNetworkType=82
        res = self.run_shell_cmd("service call phone 82")
        # print "Current network type: ",str(int(res[31],16))
        return int(res[31], 16)

    def __set_network_type(self, network_type):

        """
        Set network type

        :param network_type: identifier for the preferred network type (3G or 4G)
        :type network_type: string
        """

        if str(self.__get_network_type()) != str(network_type):
            #Nexus 6P only: setPreferredNetworkType=87
            self.run_shell_cmd("service call phone 87 i32 " + str(network_type))
            print "Current network type", self.__get_network_type(), " switch to network type ", network_type


    def __set_carrier(self, carrier_type):

        """
        Change network carriers. It returns only after successful registeration
        The function returns until successful switch

        :param carrier_type: one of "Sprint", "T-Mobile" or "Auto"
        """

        if carrier_type == "Sprint":
            #Check if the device is already in Sprint
            res = self.run_shell_cmd("getprop gsm.operator.numeric")
            if res == "310120\r\n" or res == "310000\r\n":
                return
            self.run_secret_code("34777")
            while True:
                res = self.run_shell_cmd("getprop gsm.operator.numeric")
                if res == "310120\r\n" or res == "310000\r\n":
                    break
        elif carrier_type == "T-Mobile":
            #Check if the device is already in T-Mobile
            res = self.run_shell_cmd("getprop gsm.operator.numeric")
            if res == "310260\r\n":
                return
            self.run_secret_code("34866")
            while True:
                res = self.run_shell_cmd("getprop gsm.operator.numeric")
                if res == "310260\r\n":
                    break
        elif carrier_type == "Auto":
            self.run_secret_code("342886")

    def __run_switch(self,msg):
        '''
        Perform inter-carrier selection

        :param msg: includes the target carrier network in the form of "MCCMCC-RAT"
        '''
        #TODO: migrate old code here
        tmp = msg.split("-")
        target_carrier = tmp[0]
        target_radio = tmp[1]


        #Convert network_type to specific string:
        network_type = None
        if target_radio == "4G":
            #Configure as automatic mode
            network_type = '10' #LTE/UMTS/CDMA auto
        elif target_radio == "3G":
            if target_carrier == "310260": #T-mobile 
                network_type = "0" #WCDMA preferred
            elif target_carrier == "310120" or target_carrier == "310000": #Sprint
                network_type = "4" #CDMA auto
            else: #Unsupported carrier network
                return

        self.__set_carrier(target_carrier)
        self.__set_network_type(network_type)



