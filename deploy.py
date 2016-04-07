#!/usr/bin/python
# Filename: deploy.py

'''
deploy.py

It deploys compiling environment and parameters for mobileInsight.

Author: Zengwen Yuan
        Kainan Wang
Version: 2.0
'''

import os, sys, commands, yaml


def run_config():
    commands.getstatusoutput('cp ./config/config_template.yml ./config/config.yml') 
    print 'Edit config.yml to set up the configuration'


def run_dist():
    build_dist_cmd = 'python-for-android create' \
            + ' --dist_name=' + cfg['dist_name'] \
            + ' --bootstrap=' + cfg['bootstrap'] \
            + ' --requirements=' + cfg['requirements']

    print build_dist_cmd
    os.system(build_dist_cmd)


def run_apk(build_release):
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

        zipalign_path = ""
        for subdir, dirs, files in os.walk(os.path.join(cfg['sdk_path'], 'build-tools')):
             for f in files:
                 if f == "zipalign":
                     zipalign_path = os.path.join(subdir, f)
                     break;

        align_cmd = zipalign_path + ' -v 4 ' \
            + os.path.join(cfg['p4a_path'], 'dists', cfg['dist_name'], 'bin') \
                + '/' + cfg['app_name'] + '-' + str(cfg['app_version']) + '-release-unsigned.apk ' \
            + cfg['app_name'] + '-' + str(cfg['app_version']) + '.apk'

        os.system(rm_cmd)
        os.system(build_cmd)
        os.system(sign_cmd)
        os.system(align_cmd)

        print "build command was: \n" + build_cmd
        print "sign command was: \n" + sign_cmd
        print "align command was: \n" + align_cmd
    else:
        os.system(build_cmd)
        print "build command was: \n" + build_cmd


if __name__ == '__main__':
    arg = sys.argv[1]

    try:
        debug = sys.argv[2]
    except:
        debug = ""

    try:
        with open("./config/config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
    except:
        print "Compilation environment is not configured!\nPlease modify the environment in config.yml file first."
        run_config()
        sys.exit()

    if arg == 'config':
        run_config()
    elif arg == 'dist':
        run_dist()
    elif arg == 'apk':
        if debug == "debug" or debug == "":
            run_apk(False)
        elif debug == "release":
            run_apk(True)
        else:
            print "Usage: python deploy.py apk [debug|release]"
    elif arg == 'clean':
        for subdir, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith(".pyo") or f.endswith(".DS_Store"):
                    filepath = os.path.join(subdir, f)
                    os.remove(filepath)
    elif arg == 'clean_apk':
        try:
            os.remove('./' + cfg['app_name'] + '-' + str(cfg['app_version']) + '.apk')
            os.remove('./' + cfg['app_name'] + '-' + str(cfg['app_version']) + '-debug.apk')
        except:
            print "APK clean failed."
    elif arg == 'clean_dist':
        try:
            os.system('rm -rf ' + os.path.join(cfg['p4a_path'], 'dists', cfg['dist_name']))
            os.system('rm -rf ' + os.path.join(cfg['p4a_path'], 'build', cfg['dist_name']))
            # os.system('rm -rf ' + os.path.join(cfg['p4a_path'], 'build/aars', cfg['dist_name']))
            # os.system('rm -rf ' + os.path.join(cfg['p4a_path'], 'build/javaclasses', cfg['dist_name']))
            # os.system('rm -rf ' + os.path.join(cfg['p4a_path'], 'build/libs_collections', cfg['dist_name']))
            # os.system('rm -rf ' + os.path.join(cfg['p4a_path'], 'build/python-installs', cfg['dist_name']))
            print "Dist %s successfully cleaned." % cfg['dist_name']
        except:
            print "Dist %s clean failed."
    elif arg == 'install':
        try:
            os.system('adb install -r ' + cfg['app_name'] + '-' + str(cfg['app_version']) + '.apk')
        except:
            os.system('adb install -r ' + cfg['app_name'] + '-' + str(cfg['app_version']) + '-debug.apk')
    elif arg == 'update':
        try:
            if debug == 'icellular':
                os.system('adb shell "rm -r /sdcard/mobile_insight/apps/iCellular/"')
                os.system('adb push ./internal_app/iCellular/ /sdcard/mobile_insight/apps/iCellular/')
            elif debug == 'netlogger':
                os.system('adb push ./internal_app/NetLoggerInternal/ /sdcard/mobile_insight/apps/NetLoggerInternal/')
        except:
            print "Sorry, your arguments are not supported for this moment."
