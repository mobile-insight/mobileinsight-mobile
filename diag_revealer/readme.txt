################
# readme.txt   #
# Zengwen Yuan #
# 2015-12-22   #
################

Usage guide:

1. install Android NDK
2. change directory to "./jni" folder
3. in terminal, invoke `ndk-build`, and the compiled library will be in "./libs" folder.

Sample terminal output:

jni $ clear
jni $ ndk-build
[armeabi] Compile thumb  : diag_revealer <= diag_revealer.c
[armeabi] Executable     : diag_revealer
[armeabi] Install        : diag_revealer => libs/armeabi/diag_revealer
jni $ ndk-build V=1
rm -f /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/arm64-v8a/lib*.so /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi/lib*.so /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi-v7a/lib*.so /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi-v7a-hard/lib*.so /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/mips/lib*.so /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/mips64/lib*.so /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/x86/lib*.so /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/x86_64/lib*.so
rm -f /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/arm64-v8a/gdbserver /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi/gdbserver /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi-v7a/gdbserver /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi-v7a-hard/gdbserver /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/mips/gdbserver /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/mips64/gdbserver /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/x86/gdbserver /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/x86_64/gdbserver
rm -f /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/arm64-v8a/gdb.setup /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi/gdb.setup /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi-v7a/gdb.setup /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi-v7a-hard/gdb.setup /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/mips/gdb.setup /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/mips64/gdb.setup /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/x86/gdb.setup /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/x86_64/gdb.setup
[armeabi] Compile thumb  : diag_revealer <= diag_revealer.c
/Users/Dale/Library/Android/android-ndk-r10e/toolchains/arm-linux-androideabi-4.9/prebuilt/darwin-x86_64/bin/arm-linux-androideabi-gcc -MMD -MP -MF /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/obj/local/armeabi/objs/diag_revealer/diag_revealer.o.d -fpic -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -march=armv5te -mtune=xscale -msoft-float -mthumb -Os -g -DNDEBUG -fomit-frame-pointer -fno-strict-aliasing -finline-limit=64 -I/Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/jni -DANDROID  -Wa,--noexecstack -Wformat -Werror=format-security -fPIE    -I/Users/Dale/Library/Android/android-ndk-r10e/platforms/android-19/arch-arm/usr/include -c  /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/jni/diag_revealer.c -o /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/obj/local/armeabi/objs/diag_revealer/diag_revealer.o
[armeabi] Executable     : diag_revealer
/Users/Dale/Library/Android/android-ndk-r10e/toolchains/arm-linux-androideabi-4.9/prebuilt/darwin-x86_64/bin/arm-linux-androideabi-g++ -Wl,--gc-sections -Wl,-z,nocopyreloc --sysroot=/Users/Dale/Library/Android/android-ndk-r10e/platforms/android-19/arch-arm -Wl,-rpath-link=/Users/Dale/Library/Android/android-ndk-r10e/platforms/android-19/arch-arm/usr/lib -Wl,-rpath-link=/Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/obj/local/armeabi /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/obj/local/armeabi/objs/diag_revealer/diag_revealer.o -lgcc -no-canonical-prefixes  -Wl,--no-undefined -Wl,-z,noexecstack -Wl,-z,relro -Wl,-z,now -fPIE -pie -mthumb   -lc -lm -o /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/obj/local/armeabi/diag_revealer
[armeabi] Install        : diag_revealer => libs/armeabi/diag_revealer
install -p /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/obj/local/armeabi/diag_revealer /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi/diag_revealer
/Users/Dale/Library/Android/android-ndk-r10e/toolchains/arm-linux-androideabi-4.9/prebuilt/darwin-x86_64/bin/arm-linux-androideabi-strip --strip-unneeded  /Users/Dale/Dropbox/Project/MobileInsight2/diag_revealer/libs/armeabi/diag_revealer
wifi-131-179-47-183:jni Dale$