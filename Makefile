all: apk install

# .PHONY: redist apk install  # what is this?

clean:
	python deploy.py clean

clean_apk:
	python deploy.py clean_apk

config:
	python deploy.py config

apk:
	python deploy.py apk

install:
	adb install -r "$(P4A_DIST_ROOT)/bin/MobileInsight2-0.1-debug.apk"
