P4A_ROOT=/home/dale/android/python-for-android-old_toolchain
P4A_DIST_ROOT=$(P4A_ROOT)/dist/mobile_insight2
ROOT_DIR=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUILDOZER_FLAGS=APP_ANDROID_NDK_PATH=/home/dale/android/android-ndk-r9d \
				APP_ANDROID_SDK_PATH=/home/dale/android/android-sdk-linux \
				APP_ANDROID_P4A_DIR=$(P4A_ROOT)

all: apk install

.PHONY: redist apk install

clean:
	rm -rf $(P4A_DIST_ROOT)

clean_apk:
	rm $(P4A_DIST_ROOT)/bin/MobileInsight2-0.1-debug.apk

apk:
	$(BUILDOZER_FLAGS) buildozer android debug

install:
	adb install -r "$(P4A_DIST_ROOT)/bin/MobileInsight2-0.1-debug.apk"
