# For P4A_ROOT, please keep the following three lines, and choose your own PATH when you compile

# P4A_ROOT=/Users/yuanjieli/Documents/python-for-android
# BUILDOZER_FLAGS=APP_ANDROID_NDK_PATH=/Users/yuanjieli/Documents/android-ndk \
#   				APP_ANDROID_SDK_PATH=/Users/yuanjieli/Documents/android-sdk/sdk \
#   				APP_ANDROID_NDK=8c \
#   				APP_ANDROID_SDK=14 \
#   				APP_ANDROID_P4A_DIR=$(P4A_ROOT)

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

#P4A_DIST_ROOT=$(P4A_ROOT)/dist/mobile_insight2
#ROOT_DIR=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
P4A_ROOT=/home/kainan/.local/share/python-for-android
APP_PATH=/home/kainan/code/MobileInsight2/demo_app
ANDROID_SDK_PATH=/home/kainan/env/android-sdk-linux
ANDROID_NDK_PATH=/home/kainan/env/android-ndk-r10e
ANDROID_SDK="19"
ANDROID_NDK="r10e"
WHITELIST_PATH=

all: apk install

#.PHONY: redist apk install

#clean:
#	rm -rf $(P4A_DIST_ROOT)

#clean_apk:
#	rm $(P4A_DIST_ROOT)/bin/MobileInsight2-0.1-debug.apk

apk:
	#python-for-android create --dist_name=mi2 --bootstrap=pygame --requirements=pyserial,kivy,mobileinsight
	python-for-android apk --debug --compile-pyo --private $(APP_PATH) --package edu.ucla.cs.wing --name MobileInsight2 --version 0.2 --permission INTERNET --permission WRITE_EXTERNAL_STORAGE --orientation portrait --sdk $(ANDROID_SDK) --minsdk 14 --android_api $(ANDROID_SDK) --sdk_dir $(ANDROID_SDK_PATH) --ndk_dir $(ANDROID_NDK_PATH) --ndk_version $(ANDROID_NDK) --arch armeabi --dist_name mi2


#install:
	#adb uninstall wing.cs.edu.ucla.mobile_insight2
#	adb install -r "$(P4A_DIST_ROOT)/bin/MobileInsight2-0.1-debug.apk"
