This directory incldues source codes of MobileInsight apk. 

```
.
├── README.md: this document
├── plugins: built-in plugins. Currently it includes NetLogger, RrcAnalysis and NasAnalysis
├── data: includes necessary binary executables for MobileInsight
├── service: launching MobileInsight plugins based on Android service. It is mandatory for python-for-android.
├── main.py: entrance of MobileInsight apk
├── main_ui.kv: kivy UI description for main UI
├── main_utils.py: utilities functions for MobileInsight apk
├── check_update.py: module for automatic update
├── crash_app.py: module for crash/bug report
├── log_viewer_app.py: in-app log viewer
└── settings.json: default settings for MobileInsight
```