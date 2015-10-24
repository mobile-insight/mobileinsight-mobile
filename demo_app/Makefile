P4A_ROOT=/home/likayo/Code/python-for-android
P4A_DIST_ROOT=$(P4A_ROOT)/dist/mobile_insight2
ROOT_DIR=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUILDOZER_FLAGS=APP_ANDROID_NDK_PATH=/home/likayo/android-ndk-r8c \
				APP_ANDROID_SDK_PATH=/home/likayo/Android/Sdk \
				APP_ANDROID_P4A_DIR=$(P4A_ROOT)

all: apk install

.PHONY: redist apk install

clean:
	rm -rf $(P4A_DIST_ROOT)

apk:
	$(BUILDOZER_FLAGS) buildozer android debug

install:
	adb install -r "$(P4A_DIST_ROOT)/bin/MobileInsight2-0.1-debug.apk"
