LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE    := diag_revealer
LOCAL_SRC_FILES := diag_revealer.c

include $(BUILD_EXECUTABLE)