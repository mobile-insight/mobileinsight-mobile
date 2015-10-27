__all__ = ["test_str"]

import traceback

try:
    import mobile_insight
    import mobile_insight.monitor.dm_collector.dm_collector_c as dm_collector_c
    test_str = "Loaded dm_collector_c v%s" % dm_collector_c.version
except:
    test_str = str(traceback.format_exc())
    