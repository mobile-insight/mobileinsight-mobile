# Filename: readme.txt
# Author: Zengwen Yuan
# Date: Feb 02, 2016


This directory contains codes for iCellular.

# 0x01 Structure

.
├── __init__.py							# required python script to register and import module
├── at_cmd.py 							# Send AT command to AT device
├── * bplmn_search.py 					# Backgroud PLMN search module
├── decision_strategy					# codes for decision strategy
│   ├── __init__.py 					# required python script to register and import module
│   ├── decision_strategy.py 			# An abstract decision strategy layer
│   ├── history_decision.py 			# History-based decision strategy (possible dupe)
│   ├── history_profile_example.txt 	# self-explanatory
│   ├── history_strategy.py 			# History-based decision strategy
│   └── naive_strategy.py 				# Naive strategy for selecting carrier and network type
├── * main.mi2app 						# Program entrance, relies on MobileInsight monitor
├── plmn_monitor.py 					# A wrap of bplmn_search to monitor for switch decision
├── readme.txt 							# this document
├── switch_exec.py 						# Perform switch execution
└── transaction_codes.yaml	 			# (temporary, reference purpose) secret code to call Android system service

---
* : adapted code from PC offline version; otherwise untouched yet

# 0x02 Dependencies (tentative)

	                     main.mi2app
    	                      |
    	  --------------------|--------------------
    	  |                   |                   |
    	switch             monitor            predictor
          |                   |                   |
   (fault-prevent)       plmn_search         decision_tree
          |                   |                   |
strategy-----------------bplmn_search--------------
                              |
                    mobile_insight.monitor

# 0x03 Detailed Info

+ main.mi2app

Roughly implemented decision fault prevention but the analyzer dependency needs to be reorganized

+ bplmn_search.py

Used Mobile Insight's monitor to integrate realtime info, and finished three decision fault prevention cases. Info should also be available to other modules such as decision strategy and predictor.

The real time log analysis codes are verbose here due to the fact that it is not convenient to call analyzers. I will figure out a way to modulize this script to make the analyzed cellular event reusable.

+ decision strategy

Not adapted yet

+ prediction tree

Plan to work on it right now. We need to organize and reuse the analyzed cellular event first.
