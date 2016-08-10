#!/usr/bin/python
# Filename: realtime_analyzer.py
"""
Real-time decoder, generate decoded log, save mi2log

Author: Haotian Deng
"""


from mobile_insight.analyzer.analyzer import *
from xml.dom import minidom
import datetime
import os
import mi2app_utils
from jnius import autoclass
import threading
import sys
import subprocess
import shutil

__all__=["RealtimeAnalyzer"]

class RealtimeAnalyzer(Analyzer):

    def __init__(self):

        Analyzer.__init__(self)

        self.add_source_callback(self.__msg_callback)

        if not os.path.exists("/sdcard/mobile_insight/apps/RealtimeHaotian/logs"):
            os.makedirs("/sdcard/mobile_insight/apps/RealtimeHaotian/logs")
        currentTime = datetime.datetime.now().strftime("%H%M%S_%f")
        # f = mi2app_utils.File("/sdcard/mobile_insight/apps/RealtimeHaotian/logs/log_pdsch_" + currentTime + ".csv")
        # if not f.exists():
        #     f.createNewFile()
        # self.log_pdsch = mi2app_utils.FileOutputStream(f)
        # f = mi2app_utils.File("/sdcard/mobile_insight/apps/RealtimeHaotian/logs/log_mac_" + currentTime + ".csv")
        # if not f.exists():
        #     f.createNewFile()
        # self.log_mac = mi2app_utils.FileOutputStream(f)
        # f = mi2app_utils.File("/sdcard/mobile_insight/apps/RealtimeHaotian/logs/log_rlc_" + currentTime + ".csv")
        # if not f.exists():
        #     f.createNewFile()
        # self.log_rlc = mi2app_utils.FileOutputStream(f)

        self.log_pdsch = open("/sdcard/mobile_insight/apps/RealtimeHaotian/logs/log_pdsch_" + currentTime + ".csv", "a+", 1)
        self.log_mac = open("/sdcard/mobile_insight/apps/RealtimeHaotian/logs/log_mac_" + currentTime + ".csv", "a+", 1)
        self.log_rlc = open("/sdcard/mobile_insight/apps/RealtimeHaotian/logs/log_rlc_" + currentTime + ".csv", "a+", 1)
        self.log_cmifm = open("/sdcard/mobile_insight/apps/RealtimeHaotian/logs/log_cmifm_" + currentTime + ".csv", "a+", 1)
        self.log_bler = open("/sdcard/mobile_insight/apps/RealtimeHaotian/logs/log_bler_" + currentTime + ".csv", "a+", 1)
        self.log_cqi = open("/sdcard/mobile_insight/apps/RealtimeHaotian/logs/log_cqi_" + currentTime + ".csv", "a+", 1)

    def set_source(self,source):
        """
        Set the trace source. Enable the cellular signaling messages

        :param source: the trace source (collector).
        """
        Analyzer.set_source(self,source)

        # source.enable_log("LTE_RRC_OTA_Packet")
        # source.enable_log("LTE_RRC_Serv_Cell_Info")
        # source.enable_log("LTE_RRC_MIB_Packet")
        # source.enable_log("LTE_RRC_MIB_Message_Log_Packet")
        # source.enable_log("LTE_NAS_ESM_State")
        # source.enable_log("LTE_NAS_ESM_OTA_Incoming_Packet")
        # source.enable_log("LTE_NAS_ESM_OTA_Outgoing_Packet")
        # source.enable_log("LTE_NAS_EMM_State")
        # source.enable_log("LTE_NAS_EMM_OTA_Incoming_Packet")
        # source.enable_log("LTE_NAS_EMM_OTA_Outgoing_Packet")

        # source.enable_log("LTE_PDCP_DL_Config")
        # source.enable_log("LTE_PDCP_UL_Config")
        # source.enable_log("LTE_PDCP_UL_Data_PDU")
        # source.enable_log("LTE_PDCP_DL_Ctrl_PDU")
        # source.enable_log("LTE_PDCP_UL_Ctrl_PDU")
        # source.enable_log("LTE_PDCP_DL_Stats")
        # source.enable_log("LTE_PDCP_UL_Stats")
        # source.enable_log("LTE_PDCP_DL_SRB_Integrity_Data_PDU")
        # source.enable_log("LTE_PDCP_UL_SRB_Integrity_Data_PDU")

        # source.enable_log("LTE_RLC_UL_Config_Log_Packet")
        # source.enable_log("LTE_RLC_DL_Config_Log_Packet")
        # source.enable_log("LTE_RLC_UL_AM_All_PDU")
        # source.enable_log("LTE_RLC_DL_AM_All_PDU")
        # source.enable_log("LTE_RLC_UL_Stats")
        # source.enable_log("LTE_RLC_DL_Stats")

        # source.enable_log("LTE_MAC_Configuration")
        # source.enable_log("LTE_MAC_UL_Transport_Block")
        # source.enable_log("LTE_MAC_DL_Transport_Block")
        # source.enable_log("LTE_MAC_UL_Buffer_Status_Internal")
        # source.enable_log("LTE_MAC_UL_Tx_Statistics")
        # source.enable_log("LTE_MAC_Rach_Trigger")
        # source.enable_log("LTE_MAC_Rach_Attempt")

        # source.enable_log("LTE_PHY_PDSCH_Packet")
        # source.enable_log("LTE_PHY_Serv_Cell_Measurement")
        # source.enable_log("LTE_PHY_Connected_Mode_Intra_Freq_Meas")
        # source.enable_log("LTE_PHY_Connected_Mode_Neighbor_Measurement")
        # source.enable_log("LTE_PHY_Inter_RAT_Measurement")
        # source.enable_log("LTE_PHY_Inter_RAT_CDMA_Measurement")

        # source.enable_log("LTE_PUCCH_Power_Control")
        # source.enable_log("LTE_PUSCH_Power_Control")
        # source.enable_log("LTE_PDCCH_PHICH_Indication_Report")
        # source.enable_log("LTE_PDSCH_Stat_Indication")
        # source.enable_log("LTE_PHY_System_Scan_Results")
        # source.enable_log("LTE_PHY_BPLMN_Cell_Request")
        # source.enable_log("LTE_PHY_BPLMN_Cell_Confirm")
        # source.enable_log("LTE_PHY_Serving_Cell_COM_Loop")
        # source.enable_log("LTE_PHY_PDCCH_Decoding_Result")
        # source.enable_log("LTE_PHY_PDSCH_Decoding_Result")
        # source.enable_log("LTE_PHY_PUSCH_Tx_Report")

        # source.enable_log("1xEV_Rx_Partial_MultiRLP_Packet")
        # source.enable_log("1xEV_Connected_State_Search_Info")
        # # source.enable_log("1xEV_Signaling_Control_Channel_Broadcast")
        # source.enable_log("1xEV_Connection_Attempt")
        # source.enable_log("1xEV_Connection_Release")

        # source.enable_log("WCDMA_RRC_OTA_Packet")
        # source.enable_log("WCDMA_RRC_Serv_Cell_Info")

        # source.enable_log("UMTS_NAS_OTA_Packet")
        # source.enable_log("UMTS_NAS_GMM_State")
        # source.enable_log("UMTS_NAS_MM_State")
        # source.enable_log("UMTS_NAS_MM_REG_State")

    def _save_log(self):
        orig_base_name  = os.path.basename(self.__orig_file)
        orig_dir_name   = os.path.dirname(self.__orig_file)
        milog_base_name = "diag_log_%s_%s_%s.mi2log" % (self.__log_timestamp, mi2app_utils.get_phone_info(), mi2app_utils.get_operator_info())
        milog_abs_name  = os.path.join(self.__log_dir, milog_base_name)
        shutil.copyfile(self.__orig_file, milog_abs_name)
        try:
            os.remove(self.__orig_file)
        except:
            chmodcmd = "rm -f " + self.__orig_file
            p = subprocess.Popen("su ", executable = mi2app_utils.ANDROID_SHELL, shell = True, \
                                        stdin = subprocess.PIPE, stdout = subprocess.PIPE)
            p.communicate(chmodcmd + '\n')
            p.wait()

        return milog_abs_name


    def __msg_callback(self,msg):
        # s = msg.data.decode_xml().replace("\n", "")
        # print minidom.parseString(s).toprettyxml(" ")

        if msg.type_id.find("new_diag_log") != -1:
            log_item = msg.data.decode()
            self.log_info("A new msg come in.")
            self.__log_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.__orig_file     = log_itme.get("filename")
            self.__log_dir  = mi2app_utils.get_mobile_insight_log_path()

            # FIXME (Zengwen): the change access command is a walkaround solution
            chmodcmd = "chmod 644 " + self.__orig_file
            p = subprocess.Popen("su ", executable = mi2app_utils.ANDROID_SHELL, shell = True, \
                                        stdin = subprocess.PIPE, stdout = subprocess.PIPE)
            p.communicate(chmodcmd + '\n')
            p.wait()

            self._save_log()
            self.log_info("mi2log file saved")

        elif msg.type_id == "LTE_PHY_PDSCH_Packet":
            log_item = msg.data.decode()
            bitTBS0 = int(str(log_item['TBS 0']))
            bitTBS1 = int(str(log_item['TBS 1']))
            systemFN = str(log_item['System Frame Number'])
            subFN = str(log_item['Subframe Number'])
            rntiType = str(log_item['PDSCH RNTI Type'])
            currentPdsch = str(log_item['timestamp']).split()[1]
            currentTime = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")
            arrivalTime = currentPdsch
            mcs0 = str(log_item['MCS 0'])
            mcs1 = str(log_item['MCS 1'])
            self.log_pdsch.write(str(currentPdsch) + "\t" + str(msg.type_id) + "\t" + str(currentTime) + "\t"\
                    + systemFN + "\t" + subFN + "\t" + rntiType + "\t"\
                    + str(bitTBS0) + "\t" + str(bitTBS1) + "\t" + str(mcs0) + "\t" + str(mcs1) + "\t"\
                    + str(log_item['RB Allocation Slot 0[0]']) + "\t"\
                    + str(log_item['RB Allocation Slot 0[1]']) + "\t"\
                    + str(log_item['RB Allocation Slot 1[0]']) + "\t"\
                    + str(log_item['RB Allocation Slot 1[1]']) + "\t" + "\n")
            # print str(currentPdsch) + "\t" + str(msg.type_id) + "\t" + str(bitTBS) + "\t" + str(currentTime) + "\t" + systemFN + "\t" + subFN + "\n"
            # self.list_pdsch.append(str(currentPdsch) + "\t" + str(msg.type_id) + "\t" + str(bitTBS) + "\t" + str(currentTime) + "\t" + systemFN + "\t" + subFN + "\n")
        elif msg.type_id == "LTE_MAC_DL_Transport_Block":
            log_item = msg.data.decode()
            subPkt = log_item['Subpackets'][0]
            byteDLTBS = 0
            currentTime = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")
            for sample in subPkt['Samples']:
                byteDLTBS += int(str(sample['DL TBS (bytes)']))
            byteDLTBS *= 8
            currentMacDL = str(log_item['timestamp']).split()[1]
            self.log_mac.write(str(currentMacDL) + "\t" + str(msg.type_id) + "\t" + str(byteDLTBS) + "\t" + str(currentTime) + "\n")
            # print str(currentMacDL) + "\t" + str(msg.type_id) + "\t" + str(byteDLTBS) + "\t" + str(currentTime) + "\n"
            # self.list_mac.append(str(currentMacDL) + "\t" + str(msg.type_id) + "\t" + str(byteDLTBS) + "\t" + str(currentTime) + "\n")
        elif msg.type_id == "LTE_RLC_DL_AM_All_PDU":
            log_item = msg.data.decode()
            subPkt = log_item['Subpackets'][0]
            bytePDU = 0
            currentTime = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")
            for sample in subPkt['RLCDL PDUs']:
                bytePDU += int(str(sample['pdu_bytes']))
            bytePDU *= 8
            currentRlcDL = str(log_item['timestamp']).split()[1]
            self.log_rlc.write(str(currentRlcDL) + "\t" + str(msg.type_id) + "\t" + str(bytePDU) + "\t" + str(currentTime) + "\n")
            # print str(currentRlcDL) + "\t" + str(msg.type_id) + "\t" + str(bytePDU) + "\t" + str(currentTime) + "\n"
            # self.list_rlc.append(str(currentRlcDL) + "\t" + str(msg.type_id) + "\t" + str(bytePDU) + "\t" + str(currentTime) + "\n")
        elif msg.type_id == "LTE_PHY_Connected_Mode_Intra_Freq_Meas":
            log_item = msg.data.decode()
            msgtimestamp = str(log_item['timestamp']).split()[1]
            currentTime = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")
            cellid = str(log_item['Serving Physical Cell ID'])
            rsrp = str(log_item['RSRP(dBm)'])
            rsrq = str(log_item['RSRQ(dB)'])
            earfcn = str(log_item['E-ARFCN'])
            self.log_cmifm.write(str(msgtimestamp) + "\t" + str(msg.type_id) + "\t" + str(currentTime) + "\t" + str(cellid) + "\t" + str(rsrp) + "\t" + str(rsrq) + "\t" + str(earfcn) + "\n")
        elif msg.type_id == "LTE_PHY_PUSCH_CSF":
            log_item = msg.data.decode()
            msgtimestamp = str(log_item['timestamp']).split()[1]
            currentTime = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")
            CQI0 = log_item['WideBand CQI CW0']
            CQI1 = log_item['WideBand CQI CW1']
            self.log_cqi.write(str(msgtimestamp) + "\t" + str(msg.type_id) + "\t" + str(currentTime) + "\t" + \
                    str(CQI0) + "\t" + str(CQI1) + "\n")
        elif msg.type_id == "LTE_PHY_RLM_Report":
            log_item = msg.data.decode()
            msgtimestamp = str(log_item['timestamp']).split()[1]
            currentTime = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")
            numRecords = int(log_item['Number of Records'])
            InSyncBLER = 0.0
            OutOfSyncBLER = 0.0
            for record in log_item['Records']:
                InSyncBLER += float(record['In Sync BLER (%)'])
                OutOfSyncBLER += float(record['Out of Sync BLER (%)'])
            if numRecords > 0:
                InSyncBLER = InSyncBLER / numRecords
                OutOfSyncBLER = OutOfSyncBLER / numRecords
            self.log_bler.write(str(msgtimestamp) + "\t" + str(msg.type_id) + "\t" + str(currentTime) + "\t" + \
                    str(OutOfSyncBLER) + "\t" + str(InSyncBLER) + "\n")
        # else:
        #     self.log_info(str(msg.type_id))



    def __del__(self):
        print "realtime_analyzer: close csv log files"
        try:
            self.log_pdsch.close()
            self.log_mac.close()
            self.log_rlc.close()
        except Exception as e:
            import traceback
            print str(traceback.format_exc())




