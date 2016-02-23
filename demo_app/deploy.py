#!/usr/bin/python

import os, sys, commands


def run_config():
    commands.getstatusoutput('cp config_template.py make_config.py')
    print 'Edit make_config.py to set up the configuration'

def run_apk():
    from  make_config import app_path, p4a_path, sdk_path, sdk, ndk_path, ndk

    os.system('python-for-android create --dist_name=mi2 --bootstrap=pygame --requirements=pyserial,kivy,mobileinsight')

    cmd = 'python-for-android apk --debug --compile-pyo --private ' + app_path + ' --package edu.ucla.cs.wing --name MobileInsight2 --version 0.2 --permission INTERNET --permission WRITE_EXTERNAL_STORAGE --orientation portrait --sdk ' + sdk + ' --minsdk 14 --android_api ' + sdk + ' --sdk_dir ' + sdk_path + ' --ndk_dir ' + ndk_path + ' --ndk_version ' + ndk + ' --arch armeabi --dist_name mi2 --whitelist whitelist.txt'
    print cmd
    os.system(cmd)

python-for-android apk --debug --compile-pyo --copy-libs \
--name MobileInsight2 \
--version 0.2 \
--package edu.ucla.cs.wing \
--private /Users/Dale/Workspace/mobileInsight/demo_app \
--icon /Users/Dale/Workspace/mobileInsight/demo_app/data/icon.png \
--presplash /Users/Dale/Workspace/mobileInsight/demo_app/data/presplash.jpg \
--orientation portrait \
--permission INTERNET \
--permission WRITE_EXTERNAL_STORAGE \
--sdk 19 \
--minsdk 14 \
--android_api 19 \
--sdk_dir /Users/Dale/Library/Android/sdk \
--ndk_dir /Users/Dale/Library/Android/android-ndk-r10e \
--ndk_version r10e \
--arch armeabi \
--dist_name mi2 \
--whitelist whitelist.txt

if __name__ == '__main__':
    arg =  sys.argv[1]
    if arg == 'config':
        run_config();
    if arg == 'apk':
        run_apk();

