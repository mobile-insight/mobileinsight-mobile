This directory incldues source codes of MobileInsight apk. 

.
├── README.md: this document
├── app: built-in plugins. Currently it includes NetLogger, RrcAnalysis and NasAnalysis
├── check_update.py: module for automatic update
├── crash_app.py: module for crash/bug report
├── data: it includes libraries (e.g., libwireshark) for message parsing, and necessary binary executables for MobileInsight (e.g., ws_dissector and diag_revealer)
├── log_viewer_app.py: in-app log viewer
├── main.py: entrance of MobileInsight apk
├── main_ui.kv: kivy UI description for main UI
├── main_utils.py: utilities functions for MobileInsight apk
├── service: codes for launching MobileInsight plugins based on Android service. This directory is mandatory for python-for-android.
└── settings.json: default settings for MobileInsight