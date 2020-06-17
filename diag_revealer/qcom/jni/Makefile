all: diag_revealer

# Default ndk build command. If ndk-build is not available, set the path manually.
ndk-build ?= ndk-build

diag_revealer:
	$(ndk-build)
	cp ../libs/arm64-v8a/diag_revealer .
	rm -r ../obj/ ../libs/
	cp ./diag_revealer ../../../app/data/
	echo "diag_revealer has been copied to ../../../app/data/"

clean:
	rm diag_revealer
