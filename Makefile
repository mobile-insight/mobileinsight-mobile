all: apk install

# .PHONY: redist apk install  # what is this?

clean:
	python deploy.py clean

clean_apk:
	python deploy.py clean_apk

config:
	python deploy.py config

install:
	python deploy.py install

apk:
	python deploy.py apk release

apk debug:
	python deploy.py apk debug

apk release:
	python deploy.py apk release
