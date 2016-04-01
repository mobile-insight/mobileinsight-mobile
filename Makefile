all: apk_debug install clean

.PHONY: apk install config dist debug release

config:
	python deploy.py config

dist:
	python deploy.py dist

apk:
	python deploy.py apk

apk_debug:
	python deploy.py apk debug

apk_release:
	python deploy.py apk release

install:
	python deploy.py install

clean:
	python deploy.py clean

clean_apk:
	python deploy.py clean_apk

clean_dist:
	python deploy.py clean_dist
