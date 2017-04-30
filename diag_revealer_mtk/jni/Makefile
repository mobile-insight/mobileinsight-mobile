all: diag_revealer_mtk

diag_revealer_mtk:
	ndk-build
	cp ../libs/armeabi/diag_revealer_mtk .
	rm -r ../obj/ ../libs/
	cp ./diag_revealer_mtk ../../demo_app/data/
	echo "diag_revealer_mtk has been copied to ../../demo_app/data/"

clean:
	rm diag_revealer_mtk
