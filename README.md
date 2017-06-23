# Overview #

This repository includes the code to build MobileInsight mobile version. It wraps the MobileInsight monitor and analyzer modules (`MobileInsight-core`) into an Android application, and provides key utilities (UI, log collection/viewer, protocol analyzer, plugin service etc.) to faciliate in-device use. 

The main directories include

```
.
├── README.md: this file
├── Makefile: Makefile which supports multiple compilation options
├── deploy.py: configs environments and parameters for compilation
├── config: application configurations
├── demo_app: the main directory for MobileInsight apk
├── diag_revealer: in-device raw cellular message extracter
└── resources: application icon and welcome screen
```


# Installation #

The recommend way to install the `MobileInsight-mobile` repo and configure the application compilation environment is installing a Ubuntu 16.04 development image through our provided Vagrantfile.

However, if you feel that it is necessary for you to install on your host machine, please follow the exact instructions below. We have tested these steps on macOS 10.12 and Ubuntu 14.04/16.04.

1. Prepare the compilation environment.

(a) Install our special version of `python-for-android`.

`MobileInsight-mobile` uses `python-for-android` as the building tool. We added our core functionality in to a "recipe" in the `python-for-android` repo and fixed some bugs. Our current version is based on `python-for-android` v0.4.

```shell
$ git clone https://github.com/mobile-insight/python-for-android.git
$ cd python-for-android
$ python setup.py install
```

(b) Install Android SDK. Please follow Google's official instructions at https://developer.android.com/studio/index.html.
After installation, please install following packages from the SDK manager

```
platform-19 (API-19)
platform-tools (ver. 26.0.0)
build-tools (ver. 25.0.3)
```

Then, replace the latest SDK tools `$ANDROID_SDK_HOME/tools` with a recent version of SDK tools (ver. 25.2.5) to use `ant`. You may download it from:

```
Windows: https://dl.google.com/android/repository/tools_r25.2.5-windows.zip
macOS:   https://dl.google.com/android/repository/tools_r25.2.5-macosx.zip
Linux:   https://dl.google.com/android/repository/tools_r25.2.5-linux.zip
```

Currently MobileInsight relies on exactly Android SDK API level 19 and `ant` to compile the app. We are testing the latest API level 24 and new `gradle` compilation toolchain.

(c) Install Android NDK r10e. Please download it from Google's official page at https://developer.android.com/ndk/downloads/older_releases.html. 

Currently MobileInsight relies on exactly Android NDK r10e to compile the app. We are testing the latest NDK r15 and `clang` toolchains.


2. Clone this repository.

```shell
$ git clone https://github.com/mobile-insight/mobileInsight-mobile.git
$ cd mobileInsight-mobile
```

3. Generate and customize configurations.

```shell
$ make config
```
It automatically populate the config file at `mobileInsight-mobile/config/config.yml` from the template.
Please modify the configs as necessary. Usually, you need to specify your Android SDK/NDK and python-for-android storage path. 

4. Compile the MobileInsight distribution for python-for-android.

```shell
$ make dist
```

It may take few minutes depending on the network connection speed but is only required for the first time.
More details on distribution can be found on `python-for-android`'s documentation (https://python-for-android.readthedocs.io/en/latest/quickstart/#distribution-management)

5. Compile MobileInsight apk and install

```shell
$ make apk_debug
$ adb install MobileInsight-<ver>-debug.apk
```

These commands will build a debug version of the MobileInsight apk and install to your phone using `adb`.

Note that, to make a release version, you need to specify your own signing keystore. Specify the path to your keystore and use `make apk_release` instead.

Yay! So far, you should have successfully built a vanilla version of the MobileInsight app. Play around and if you want to apply modifications, you just need to repeat step 5.
For other usages, please refer to our advanced topics on wiki.
