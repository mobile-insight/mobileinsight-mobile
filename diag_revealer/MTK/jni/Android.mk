LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE    := diag_revealer_mtk
LOCAL_SRC_FILES := diag_revealer_mtk.c
LOCAL_LDLIBS    := -L$(SYSROOT)/usr/lib -llog

include $(BUILD_EXECUTABLE)
