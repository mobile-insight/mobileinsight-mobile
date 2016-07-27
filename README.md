# Overview #
This repository includes the code of MobileInsight mobile version. It wraps the MobileInsight monitor/analyzer modules into the device, and provides some key utilities (UI, diag_revealer, plugin service, logviewer, etc.) to faciliate in-device use. 

mobileInsight-mobile is built on top of python-for-android. It depends on mobileInsight-desktop for the core MobileInsight monitor/analyzer modules. To compile it, you need also install Android sdk-v19, and Android ndk-r10e. 

The main directories include

```
.
├── Makefile: makefile for compiling the app, building python-for-android distribution
├── README.md: this file
├── config: configurations for the compilation
├── demo_app: the main directory for MobileInsight apk
├── deploy.py: utilities to faciliate compilation
├── diag_revealer: in-device raw cellular message extracter
├── docs: documentation
├── internal_app: some experimental MobileInsight plugins
└── resources: icons, welcome screens, etc.
```


# How to install #

First install python-for-android from

```shell
$ git clone https://wing1.cs.ucla.edu/gitlab/zyuan/python-for-android.git
$ cd python-for-android
$ sudo python setup.py install
```

Then clone this repository

```shell
$ git clone https://wing1.cs.ucla.edu/gitlab/root/mobileInsight-mobile.git
$ cd mobileInsight-mobile
$ make config
```
After the configuration, please modify `mobileInsight-mobile/config/config.yml` to specify Android SDK/NDK and Python-for-android paths, build version, etc. 

Then compile the distribution (only run it first time)

```shell
$ make dist
```

Last compile the apk

```shell
$ make apk_debug/release
```

Note that, to make release version, you are required for the release key (please contact Yuanjie or Zengwen for the key).

So far, you should have successfully built the debug version of MobileInsight2 app. Install it on Android phone is easy:

```shell
$ adb install -r MobileInsight-<ver>-debug.apk
```

To build an APK for release, use `make apk_release` instead.

# How to contribute #

+ Do not push to `master` branch directly. It should serve as the stable branch
+ For any changes, please first merge to dev-x.y.z branch. Then before the release, we will merge it to the master branch 
+ Any change should open a new branch first
+ After testing, submit a merge request
