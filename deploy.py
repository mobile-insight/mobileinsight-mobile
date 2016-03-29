#!/usr/bin/python

import os, sys, commands
import yaml


def run_config():
    commands.getstatusoutput('cp config_template.yml config.yml') 
    print 'Edit config.yml to set up the configuration'


def run_apk(build_release):
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    build_dist_cmd = 'python-for-android create' \
            + ' --dist_name=' + cfg['dist_name'] \
            + ' --bootstrap=' + cfg['bootstrap'] \
            + ' --requirements=' + cfg['requirements']

    build_cmd = 'python-for-android apk' \
            + ' --compile-pyo' \
            + ' --copy-libs' \
            + ' --name=' + cfg['app_name'] \
            + ' --version=' + str(cfg['app_version']) \
            + ' --private=' + cfg['app_path'] \
            + ' --package=' + cfg['pkg_name'] \
            + ' --permission INTERNET' \
            + ' --permission WRITE_EXTERNAL_STORAGE' \
            + ' --icon=' + cfg['icon_path'] \
            + ' --presplash=' + cfg['presplash_path'] \
            + ' --orientation=' + cfg['orientation'] \
            + ' --sdk=' + str(cfg['sdk_version']) \
            + ' --minsdk=' + str(cfg['minsdk']) \
            + ' --android_api=' + str(cfg['api_level']) \
            + ' --sdk_dir=' + cfg['sdk_path'] \
            + ' --ndk_dir=' + cfg['ndk_path'] \
            + ' --ndk_version=' + str(cfg['ndk_version']) \
            + ' --arch=' + cfg['arch'] \
            + ' --dist_name=' + cfg['dist_name'] \
            + ' --whitelist=' + cfg['whitelist']

    if build_release is True:
        build_cmd = build_cmd + "--release" \
                + ' --keystore=' + cfg['keystore']\
                + ' --signkey=' + cfg['signkey']\
                + ' --keystorepw=' + cfg['keystorepw']\
                + ' --signkeypw=' + cfg['signkeypw']

    print build_dist_cmd
    os.system(build_dist_cmd)

    print build_cmd
    os.system(build_cmd)

if __name__ == '__main__':
    arg = sys.argv[1]
    try:
        debug = sys.argv[2]
    except:
        debug = ""

    if arg == 'config':
        run_config()
    elif arg == 'apk':
        # TODO:
        # support debug version and release version
        if debug == "debug" or debug == "":
            run_apk(False)
        elif debug == "release":
            run_apk(True)
        else:
            print "Usage: python deploy.py apk [debug|release]"
    elif arg == 'clean':
        # TODO
        # finish clean up script
        # mainly clean the pyo files
        pass

