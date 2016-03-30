all: apk_release install clean

.PHONY: apk install

clean:
	python deploy.py clean

clean_apk:
	python deploy.py clean_apk

clean_dist:
	python deploy.py clean_dist

config:
	python deploy.py config

install:
	python deploy.py install

apk:
	python deploy.py apk

apk_debug:
	python deploy.py apk debug

apk_release:
	python deploy.py apk release
