#!/bin/bash

# version of your package
VERSION_mobile_insight=${VERSION_mobile_insight:-1.0}

# dependencies of this recipe
DEPS_mobile_insight=()

# url of the package
URL_mobile_insight=

# md5 of the package
MD5_mobile_insight=

# default build path
BUILD_mobile_insight=$BUILD_PATH/mobile_insight/mobile_insight

# default recipe path
RECIPE_mobile_insight=$RECIPES_PATH/mobile_insight

# function called for preparing source code if needed
# (you can apply patch etc here.)
function prebuild_mobile_insight() {
	cd $BUILD_PATH/mobile_insight

	rm -rf mobile_insight
	if [ ! -d mobile_insight ]; then
		try cp -fr $RECIPE_mobile_insight/src $BUILD_mobile_insight
	fi
}

# function called to build the source code
function build_mobile_insight() {
	cd $BUILD_mobile_insight

	push_arm

    export CFLAGS="$CFLAGS -I$ANDROIDNDK/sources/cxx-stl/gnu-libstdc++/$TOOLCHAIN_VERSION/include -I$ANDROIDNDK/sources/cxx-stl/gnu-libstdc++/$TOOLCHAIN_VERSION/libs/armeabi/include"
    export LDFLAGS="$LDFLAGS -L$ANDROIDNDK/sources/cxx-stl/gnu-libstdc++/$TOOLCHAIN_VERSION/libs/armeabi -lgnustl_shared"

#	export LDFLAGS="$LDFLAGS -L$LIBS_PATH"
#	export LDSHARED="$LIBLINK"

	# fake try to be able to cythonize generated files
	$HOSTPYTHON setup.py build_ext
	try find . -iname '*.pyx' -exec cython {} \;
	try $HOSTPYTHON setup.py build_ext -v
	# try find build/lib.* -name "*.o" -exec $STRIP {} \;
	try $HOSTPYTHON setup.py install -O2

	try rm -rf $BUILD_PATH/python-install/lib/python*/site-packages/mobile_insight/tools
    try cp $ANDROIDNDK/sources/cxx-stl/gnu-libstdc++/$TOOLCHAIN_VERSION/libs/armeabi/libgnustl_shared.so $LIBS_PATH/

#	unset LDSHARED
	pop_arm
}

# function called after all the compile have been done
function postbuild_mobile_insight() {
	true
}
