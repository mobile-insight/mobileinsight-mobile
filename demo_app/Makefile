P4A_ROOT=/home/likayo/Code/python-for-android
P4A_DIST_ROOT=$(P4A_ROOT)/dist/default
ROOT_DIR=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

all: apk install

.PHONY: redist apk install

redist:
	cd "$(P4A_ROOT)" ; \
	./distribute.sh -m "kivy mobile_insight" ; \
	cd "$(ROOT_DIR)"

apk:
	cd "$(P4A_DIST_ROOT)" ; \
	python ./build.py \
		--package org.wing.mobile_insight \
		--name "MobileInsight2" \
		--version 1.0 \
		--dir "$(ROOT_DIR)" \
		--orientation portrait \
		debug ; \
	cd "$(ROOT_DIR)"

install:
	sudo adb install -r "$(P4A_DIST_ROOT)/bin/MobileInsight2-1.0-debug.apk"
