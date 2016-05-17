# How to install #

First install python-for-android from

```shell
$ git clone https://wing1.cs.ucla.edu/gitlab/zyuan/python-for-android.git
$ cd python-for-android
$ sudo python setup.py install
```

Then clone this repository

```shell
$ git clone https://wing1.cs.ucla.edu/gitlab/root/MobileInsight2.git
$ cd MobileInsight2
$ make config
$ make dist
$ make apk
```

So far, you should have successfully built the debug version of MobileInsight2 app. Install it on Android phone is easy:

```shell
$ adb install -r MobileInsight-<ver>-debug.apk
```

To build an APK for release, use `make apk_release` instead.

# How to contribute #

+ Keep `master` branch as the stable branch
+ Any change should open a new branch first
+ After testing, submit a merge request
