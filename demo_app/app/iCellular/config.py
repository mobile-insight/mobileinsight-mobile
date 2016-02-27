#!/usr/bin/python
# Filename: config.py

"""
Configurations for common paths

Author: Yuanjie Li
"""

#carrier networks that device is interested in
monitor_list = ["310260-4G", "310260-3G", "310120-4G", "310120-3G"]	
#AT command port
at_serial_port = "/dev/smd11"	
#decision strategy used
decision_strategy = "TestStrategy"	