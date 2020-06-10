all: diag_revealer_mtk
# Default ndk build command. If ndk-build is not available, set the path manually.
ndk-build ?= ndk-build

diag_revealer:
	$(ndk-build)
	cp ../libs/arm64-v8a/diag_revealer .
	cp ../libs/arm64-v8a/diag_revealer_mtk .
	rm -r ../obj/ ../libs/
	cp ./diag_revealer_mtk ../../../app/data/
	echo "diag_revealer_mtk has been copied to ../../../app/data/"

clean:
	rm diag_revealer_mtk
