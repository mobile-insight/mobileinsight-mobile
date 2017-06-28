all: diag_revealer

diag_revealer:
	ndk-build
	cp ../libs/armeabi/diag_revealer .
	rm -r ../obj/ ../libs/
	cp ./diag_revealer ../../../app/data/
	echo "diag_revealer has been copied to ../../../app/data/"

clean:
	rm diag_revealer
