#!/usr/bin/python

import os, sys, commands
# from os.path import exists, join,
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

    print build_dist_cmd
    os.system(build_dist_cmd)

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
        # This should work but currently has bug
        # build_cmd = build_cmd + ' --release' \
        #         + ' --keystore=' + str(cfg['keystore']) \
        #         + ' --signkey=' + str(cfg['signkey']) \
        #         + ' --keystorepw=' + str(cfg['keystorepw']) \
        #         + ' --signkeypw=' + str(cfg['signkeypw'])

        rm_cmd = 'rm ' + cfg['app_name'] + '-' + str(cfg['app_version']) + '.apk'
        build_cmd = build_cmd + ' --release'
        sign_cmd = 'jarsigner -verbose' \
            + ' -sigalg SHA1withRSA' \
            + ' -digestalg SHA1' \
            + ' -keystore ' + cfg['keystore'] \
            + ' ' + os.path.join(cfg['p4a_path'], 'dists', cfg['dist_name'], 'bin') \
                + '/' + cfg['app_name'] + '-' + str(cfg['app_version']) + '-release-unsigned.apk ' + cfg['signkey']
        align_cmd = 'zipalign -v 4 ' \
            + os.path.join(cfg['p4a_path'], 'dists', cfg['dist_name'], 'bin') \
                + '/' + cfg['app_name'] + '-' + str(cfg['app_version']) + '-release-unsigned.apk ' \
            + cfg['app_name'] + '-' + str(cfg['app_version']) + '.apk'

        print build_cmd
        print sign_cmd
        print align_cmd
        os.system(rm_cmd)
        os.system(build_cmd)
        os.system(sign_cmd)
        os.system(align_cmd)
    else:
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
    elif arg == 'install':
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
        try:
            os.system('adb install -r ' + cfg['app_name'] + '-' + str(cfg['app_version']) + '.apk')
        except:
            os.system('adb install -r ' + cfg['app_name'] + '-' + str(cfg['app_version']) + '-debug.apk')
