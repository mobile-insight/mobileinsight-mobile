all: diag_revealer

diag_revealer:
	ndk-build
	cp ../libs/armeabi/diag_revealer .
	rm -r ../obj/ ../libs/
	cp ./diag_revealer ../../../demo_app/data/
	echo "diag_revealer has been copied to ../../../demo_app/data/"

clean:
	rm diag_revealer
