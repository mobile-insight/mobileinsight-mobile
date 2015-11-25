#!/usr/bin/python
# Filename: switch_exec.py

"""
Perform inter-carrier switch execution. Responsible for availability and continuity

Author: Yuanjie Li
"""

import os

class SwitchExec:

    def __init__(self):
        pass

    def run_shell_cmd(self,cmd):
        """
            Run an adb shell command (as root)

            :param cmd: the command to be executed
            :returns: the results of the command
        """
        return os.popen("su -c " + cmd).read()


    def run_secret_code(self,code):
        """
            Dial a secret code in Android

            :param code: the secret code to dail
        """

        self.run_shell_cmd("am broadcast -a \"android.provider.Telephony.SECRET_CODE\" -d \"android_secret_code://" + code + "\"")

    def get_network_type(self):
        """
            Return a current network type
        """
        #Nexus 6P only: setPreferredNetworkType=82
        res = self.run_shell_cmd("service call phone 82")
        # print "Current network type: ",str(int(res[31],16))
        return int(res[31], 16)


    def set_network_type(self, network_type):

        """
            Set network type

            :param network_type: identifier for the preferred network type
        """

        if str(self.get_network_type()) != str(network_type):
            #Nexus 6P only: setPreferredNetworkType=87
            self.run_shell_cmd("service call phone 87 i32 " + str(network_type))
            print "Current network type", self.get_network_type(), " switch to network type ", network_type
        

    def set_carrier(self, carrier_type):

        """
            Change network carriers. It returns only after successful registeration

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

    def switch_to(self,target):
        """
            Perform PLMN switch to the target carrier and network type

            :param target: a (carrier,network_type) pair
        """
        if target is None:
            return
        #TODO: perform the switch until the device is idle
        self.set_carrier(target[0])
        self.set_network_type(target[1])


if __name__=="__main__":

	switch = SwitchExec(ADB_SHELL_PATH)

	switch.set_carrier("T-Mobile")

