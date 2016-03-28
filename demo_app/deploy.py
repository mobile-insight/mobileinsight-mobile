#!/usr/bin/python

import os, sys, commands


def run_config():
    commands.getstatusoutput('cp config_template.py make_config.py')
    print 'Edit make_config.py to set up the configuration'


def run_apk():
    from make_config import *

    build_dist_cmd = 'python-for-android create'
            + ' --dist_name=' + dist_name \
            + ' --bootstrap=' + bootstrap \
            + ' --requirements=' + requirements

    build_cmd = 'python-for-android apk' \
            + ' --debug' \
            + ' --compile-pyo' \
            + ' --copy-libs' \
            + ' --name' + app_name \
            + ' --version' + app_version \
            + ' --private' + app_path \
            + ' --package' + pkg_name \
            + ' --permission INTERNET' \
            + ' --permission WRITE_EXTERNAL_STORAGE' \
            + ' --icon' + icon_path \
            + ' --presplash' + presplash_path \
            + ' --orientation' + orientation \
            + ' --sdk' + sdk_version \
            + ' --minsdk' + minsdk \
            + ' --android_api' + api_level \
            + ' --sdk_dir' + sdk_path \
            + ' --ndk_dir' + ndk_path \
            + ' --ndk_version' + ndk_version \
            + ' --arch' + arch \
            + ' --dist_name' + dist_name \
            + ' --whitelist' + whitelist

    print build_dist_cmd
    os.system(build_dist_cmd)

    print build_cmd
    os.system(build_cmd)

if __name__ == '__main__':
    arg = sys.argv[1]
    if arg == 'config':
        run_config();
    elif arg == 'apk':
        # TODO:
        # support debug version and release version
        run_apk();
    elif arg == 'clean':
        # TODO
        # finish clean up script
        # mainly clean the pyo files
        pass

