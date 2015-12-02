# For P4A_ROOT, please keep the following three lines, and choose your own PATH when you compile

P4A_ROOT=/Users/yuanjieli/Documents/python-for-android
BUILDOZER_FLAGS=APP_ANDROID_NDK_PATH=/Users/yuanjieli/Documents/android-ndk \
  				APP_ANDROID_SDK_PATH=/Users/yuanjieli/Documents/android-sdk/sdk \
  				APP_ANDROID_NDK=8c \
  				APP_ANDROID_SDK=14 \
  				APP_ANDROID_P4A_DIR=$(P4A_ROOT)

#P4A_ROOT=/home/dale/android/python-for-android-old_toolchain
#BUILDOZER_FLAGS=APP_ANDROID_NDK_PATH=/home/dale/android/android-ndk-r9d \
#				APP_ANDROID_SDK_PATH=/home/dale/android/android-sdk-linux \
#				APP_ANDROID_NDK=9d \
#				APP_ANDROID_SDK=19 \
#				APP_ANDROID_P4A_DIR=$(P4A_ROOT)

# P4A_ROOT=/home/likayo/Code/python-for-android
# BUILDOZER_FLAGS=APP_ANDROID_NDK_PATH=/home/likayo/android-ndk-r8c \
# 				APP_ANDROID_SDK_PATH=/home/likayo/Android/Sdk \
# 				APP_ANDROID_NDK=8c \
# 				APP_ANDROID_SDK=14 \
# 				APP_ANDROID_P4A_DIR=$(P4A_ROOT)

P4A_DIST_ROOT=$(P4A_ROOT)/dist/mobile_insight2
ROOT_DIR=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))


all: apk install

.PHONY: redist apk install

clean:
	rm -rf $(P4A_DIST_ROOT)

clean_apk:
	rm $(P4A_DIST_ROOT)/bin/MobileInsight2-0.1-debug.apk

apk:
	$(BUILDOZER_FLAGS) buildozer android debug

install:
	adb uninstall org.ucla.wing.mobile_insight2
	adb install -r "$(P4A_DIST_ROOT)/bin/MobileInsight2-0.1-debug.apk"
