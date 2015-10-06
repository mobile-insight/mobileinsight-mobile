app_log = ""

import os
import shlex
import subprocess
import time

# The subprocess module uses "/bin/sh" by default, which must be changed on Android.
# See http://grokbase.com/t/gg/python-for-android/1343rm7q1w/py4a-subprocess-popen-oserror-errno-8-exec-format-error
ANDROID_SHELL = "/system/bin/sh"

log_dir = "/sdcard/external_sd/mobile_insight_log"
qmdls_before = set(os.listdir(log_dir))

cmd1 = "su -c diag_mdlog -s 1 -o \"%s\"" % log_dir
subprocess.Popen(cmd1, executable=ANDROID_SHELL, shell=True)

# time.sleep(60.0)

# diag_procs = []
# pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
# for pid in pids:
#     try:
#         cmdline = open(os.path.join("/proc", pid, "cmdline"), "rb").read()
#         if cmdline.startswith("diag_mdlog"):
#             diag_procs.append(int(pid))
#     except IOError:
#         continue

# if len(diag_procs) > 0:
#     cmd2 = "su -c kill -9 " + " ".join([str(pid) for pid in diag_procs])
#     subprocess.Popen(cmd2, executable=ANDROID_SHELL, shell=True)
#     app_log += cmd2 + "\n"

qmdls_after = set(os.listdir(log_dir))

# app_log += str(qmdls_before) + "\n"
# app_log += str(sorted(list(qmdls_after - qmdls_before))) + "\n"

log_file = sorted(list(qmdls_after))[-1]

from mobile_insight.monitor import QmdlReplayer
from mobile_insight.analyzer import MmAnalyzer

src = QmdlReplayer({"ws_dissect_executable_path": "/data/likayo/android_pie_ws_dissector",
                    "libwireshark_path": "/data/likayo/"})
mm = MmAnalyzer()

src.set_input_path(os.path.join(log_dir, log_file))
mm.set_source(src)

m.set_source(src)

# Start the monitoring
src.run()
