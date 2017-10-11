MobileInsight Mobile Version
==============

This repository includes the codes to build MobileInsight mobile version. It wraps the MobileInsight monitor and analyzer modules (`mobileinsight-core`) into an Android application, and provides key utilities (UI, log collection/viewer, protocol analyzer, plugin service etc.) to faciliate in-device use. 

The structure of this repo is organized as follows:

```
.
├── README.md: this file
├── Makefile: supports multiple compilation options, see usage
├── deploy.py: configures compilation environments
├── config: codes for application specific configurations
├── app: main directory for the MobileInsight app
├── diag_revealer: in-device raw cellular message extracter
└── resources: application icon and welcome screen
```


## Quickstart

It is strongly recommended to use the standalone Vagrant configuration file to automatically download `mobileinsight-mobile` repo and configure the development environment. The `Vagrantfile` will automatically fire up a virtual machine and configure everything. It is tested on Ubuntu 14.04/16.04, macOS 10.11/10.12, and Windows 7/10.

First, install `virtualbox` and `vagrant`. You can follow the instructions at [VirtuBox.org](https://www.virtualbox.org) and [Vagrant](https://www.vagrantup.com).

Second, obtain the newest `Vagrantfile` for MobileInsight development from the [release page](https://github.com/mobile-insight/mobileinsight-dev/releases). You should put it under your development path, say `/path/to/dev`. Run the `Vagrantfile` and install the virtual image using `vagrant up`. 

```
cd /path/to/dev
curl -s https://api.github.com/repos/mobile-insight/mobileinsight-dev/releases/latest | grep tarball_url | cut -d '"' -f 4 | xargs wget
mv v* mi.tgz
tar xf mi.tgz -C . --strip-components=1
rm mi.tgz
vagrant up
```

Depending on the network and CPU speed, the installation may take half hour or longer.

Then, when the process finish install and returns the shell, a MobileInsight app is already compiled and copied to your path (`/path/to/dev`). You can install it on supported Android phone and try it out immediately using `adb` (for example, the compiled APK version is 3.2.0).

```
adb install MobileInsight-3.2.0-debug.apk
```

For more details on using the provided `Vagrantfile` to configure the MobileInsight, please refer to the [`mobileinsight-dev` repo](https://github.com/mobile-insight/mobileinsight-dev).


## Usage

Once the development virtual machine is installed, you can login and recompile the app with your customized changes.

First, run `vagrant ssh` to login to the virtual machine.

```
(host shell) $ cd /path/to/dev
(vm shell)   $ vagrant ssh
(vm shell)   $ cd mi-dev
```

By default, MobileInsight repos are installed under the `/home/vagrant/mi-dev` folder.
The version and icon of the MobileInsight app are configured by the `config/config.yml` file.
Edit this file to specify the version, API level and NDK used for your own need.
Next, you can compile the new APK (debug version) using `make`:

```
make apk_debug
```

If you want to sign your application, you need to specify the correct keystore, private key and their passwords in `config/config.yml` file, and use

```
make apk_release
```

We have provided an example keystore at `config/example.jks`. The passwords are:

```
Passphrase for keystore: mobileinsight
Key password for mi3: mobileinsight
```

The compiled APK can be copied out of the virtual machine by copying to the `/vagrant` folder.
You may install the APK to phone after that.

```
(vm shell)   $ cp MobileInsight-3.2.0-debug.apk /vagrant
(vm shell)   $ exit
(host shell) $ adb install -r MobileInsight-3.2.0-debug.apk
```

__NOTE__: If upstream core functionalities of MobileInsight ([`mobileinsight-core`](https://github.com/mobile-insight/mobileinsight-core)) changes, you need to clean the existing MobileInsight *distribution* and re-compile it:

```
make clean_dist
make dist
```

The newly compiled distribution will be called `<dist_name>` (in `config/config.yml`) and stored under `<p4a_path>/dists/<dist_name>`.
These steps are only required to be performed once if the core functionalities changes. More details on distribution can be found in [`python-for-android`'s documentation](https://python-for-android.readthedocs.io/en/latest/quickstart/#distribution-management).


## Manual Installation

The recommended way to install the `mobileinsight-mobile` repo and set up the environment is through our provided `Vagrantfile`. However, if you need to install and configure it on your host machine for performance or whatever reason, please follow the __exact__ instructions below. We have tested these steps on macOS 10.12 and Ubuntu 14.04/16.04.

1. Install the special version of `python-for-android`.

`mobileinsight-mobile` uses `python-for-android` as the backend building tool. We added a `mobileinsight` **recipe** into the `python-for-android` repo and fixed some bugs to support the core functionality of `mobileinsight-core`.


```
git clone https://github.com/mobile-insight/python-for-android.git
cd python-for-android
python setup.py install
```

2. Install Android SDK.

Please follow [Google's official instructions](https://developer.android.com/studio/index.html). Please install following packages using the SDK manager:

```
platform-19 (API-19)
platform-tools (ver. 26.0.0)
build-tools (ver. 25.0.3)
```

If the installed SDK tool version is higher than `v25.2.5`, replace the latest SDK tools `$ANDROID_SDK_HOME/tools` with SDK tools version 25.2.5 to use `ant`. You may download it from:

```
Windows: https://dl.google.com/android/repository/tools_r25.2.5-windows.zip
macOS:   https://dl.google.com/android/repository/tools_r25.2.5-macosx.zip
Linux:   https://dl.google.com/android/repository/tools_r25.2.5-linux.zip
```

Currently MobileInsight relies on __exactly__ Android SDK API level 19 and `ant` to compile the app. We are testing the latest API level 25 and new `gradle` compilation toolchain.

3. Install Android NDK r10e.

Please download the __exact__ version of Android NDK r10e from [Google's archive page](https://developer.android.com/ndk/downloads/older_releases.html). Currently MobileInsight relies on  __exactly__ Android NDK r10e to compile the app. We are testing the latest NDK r15 and also the `clang` instead of `gcc`.

4. Install other dependencies.

MobileInsight mobile version compilation dependends `python-for-android`, which requires:

+ git
+ build-essential
+ ant
+ python2
+ cython (version 0.25.2)
+ a Java JDK
+ zlib (including 32 bit)
+ libncurses (including 32 bit)
+ libtool
+ unzip
+ virtualenv
+ ccache
+ PyYaml
+ xmltodict

On Ubuntu, you can install them with

```
apt-get -y install build-essential git unzip ant ccache
apt-get -y install autoconf automake
apt-get -y install zlib1g-dev libtool ccache
apt-get -y install openjdk-8-jdk openjdk-8-jre
apt-get -y install python2.7-dev python-setuptools
apt-get -y install libc6:i386 libncurses5:i386 libstdc++6:i386 libbz2-1.0:i386 lib32z1 zlib1g:i386
pip install cython==0.25.2
pip install pyyaml xmltodict
```

On macOS, you can install them with [Homebrew](https://brew.sh), such as:

```
brew cask install java
brew install git python zlib libtool ant ccache autoconf automake
pip2 install cython==0.25.2
pip2 install pyyaml xmltodict
```

5. Clone this repository and create config file.

```
git clone https://github.com/mobile-insight/mobileinsight-mobile.git
cd mobileinsight-mobile
make config
nano config/config.yml
```

You need to cutomize the configurations, especially specifying the path of your Android SDK/NDK and `python-for-android` storage path. 
Then, you can follow the usage guide and compile the application. Basically, you can invoke

```
make dist
make app_debug
```

## How to Contribute

We love pull requests and novel ideas. You can open issues here to report bugs. Feel free to improve MobileInsight and become a collaborator if you are interested.

The following Slack group is used exclusively for discussions about developing the MobileInsight and its sister projects:

+ Dev Slack Group: https://mobileinsight-dev.slack.com (join via this [link](https://goo.gl/htJGqT))
+ Email: support@mobileinsight.net

For other advanced topics, please refer to the wiki and the [MobileInsight website](http://mobileinsight.net).
