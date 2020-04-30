all: diag_revealer_mtk

diag_revealer_mtk:
	ndk-build
	cp ../libs/arm64-v8a/diag_revealer_mtk .
	rm -r ../obj/ ../libs/
	cp ./diag_revealer_mtk ../../../app/data/
	echo "diag_revealer_mtk has been copied to ../../../app/data/"

clean:
	rm diag_revealer_mtk
