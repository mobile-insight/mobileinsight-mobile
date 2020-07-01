all: apk_release install clean

.PHONY: apk install config dist debug release

config:
	python3 deploy.py config

dist:
	python3 deploy.py dist

apk:
	python3 deploy.py apk

apk_debug:
	python3 deploy.py apk debug

apk_release:
	python3 deploy.py apk release

install:
	python3 deploy.py install

clean_all:
	python3 deploy.py clean_all

clean:
	python3 deploy.py clean

clean_apk:
	python3 deploy.py clean_apk

clean_dist:
	python3 deploy.py clean_dist
