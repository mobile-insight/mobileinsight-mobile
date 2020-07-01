#!/usr/bin/python
# Filename: deploy.py

'''
deploy.py

It deploys compiling environment and parameters for mobileinsight.

Authors : Zengwen Yuan
          Kainan Wang
Version : 2.4 -- 2017/10/05 automate password arguments for release version
          2.3 -- 2017/09/25 remove obselete 'compile-pyo' option
          2.2 -- 2016/05/17 add config commands to copy libs
          2.1 -- 2016/05/16 reformat building commands
'''

import os
import sys
import yaml
import subprocess
import subprocess

LIBS_GIT = 'https://github.com/mobile-insight/mobileinsight-libs.git'

def run_config():
    os.system(
        'git clone {}'.format(LIBS_GIT))
    if os.path.isdir('./app/data') is False:
        os.makedirs('./app/data')
    os.system('cp mobileinsight-libs/lib/* ./app/data')
    os.system('cp mobileinsight-libs/bin/* ./app/data')
    os.system('rm -rf mobileinsight-libs')
    if os.path.isfile('./config/config.yml') is True:
        os.system('cp ./config/config.yml ./config/config.yml.bak')
    os.system('tail -n+8 ./config/config_template.yml > ./config/config.yml')
    print('Edit ./config/config.yml to customize your configuration!')

def run_dist():
    build_dist_cmd = 'python-for-android create' \
        + ' --dist-name={}'.format(cfg['dist_name']) \
        + ' --bootstrap={}'.format(cfg['bootstrap']) \
        + ' --storage-dir={}'.format(cfg['p4a_path']) \
        + ' --sdk-dir={}'.format(cfg['sdk_path']) \
        + ' --android-api={}'.format(cfg['api_level']) \
        + ' --ndk-dir={}'.format(cfg['ndk_path']) \
        + ' --arch={}'.format(cfg['arch']) \
        + ' --requirements={}'.format(cfg['requirements'])

    print(build_dist_cmd)
    os.system(build_dist_cmd)


def run_apk(build_release):

    make_diag_cmd = 'cd diag_revealer/qcom/jni; ' \
                      + 'rm diag_revealer; ' \
                      + 'make ndk-build={}/ndk-build; '.format(cfg['ndk_path']) \
                      + 'cd ../../mtk/jni; ' \
                      + 'rm diag_revealer_mtk; ' \
                      + 'make ndk-build={}/ndk-build; '.format(cfg['ndk_path'])

    build_cmd = 'python-for-android apk' \
        + ' --copy-libs' \
        + ' --name={}'.format(cfg['app_name']) \
        + ' --dist-name={}'.format(cfg['dist_name']) \
        + ' --storage-dir={}'.format(cfg['p4a_path']) \
        + ' --version={}'.format(cfg['app_version']) \
        + ' --private={}/{}'.format(cfg['mi_dev_path'], cfg['app_path']) \
        + ' --package={}'.format(cfg['pkg_name']) \
        + ' --icon={}/{}'.format(cfg['mi_dev_path'], cfg['icon_path']) \
        + ' --presplash={}/{}'.format(cfg['mi_dev_path'], cfg['presplash_path']) \
        + ' --orientation={}'.format(cfg['orientation']) \
        + ' --sdk-dir={}'.format(cfg['sdk_path']) \
        + ' --android-api={}'.format(cfg['api_level']) \
        + ' --ndk-dir={}'.format(cfg['ndk_path']) \
        + ' --arch={}'.format(cfg['arch']) \
        + ' --window'\
        + ' --whitelist={}/{}'.format(cfg['mi_dev_path'], cfg['whitelist']) \
        + ' --permission WRITE_EXTERNAL_STORAGE' \
        + ' --permission READ_EXTERNAL_STORAGE' \
        + ' --permission INTERNET' \
        + ' --permission RECEIVE_BOOT_COMPLETED' \
        + ' --permission ACCESS_WIFI_STATE' \
        + ' --permission INSTALL_PACKAGES' \
        + ' --permission ACCESS_NETWORK_STATE' \
        + ' --permission ACCESS_FINE_LOCATION' \
        + ' --permission ACCESS_COARSE_LOCATION'
    # + ' --intent-filters BOOT_COMPLETED'

    if build_release is True:
        clean_cmd = 'rm {}-{}.apk'.format(cfg['app_name'], cfg['app_version'])

        build_cmd = build_cmd + ' --release' \
                + ' --keystore={}'.format(cfg['keystore']) \
                + ' --keystorepw={}'.format(cfg['keystorepw']) \
                + ' --signkey={}'.format(cfg['signkey']) \
                + ' --signkeypw={}'.format(cfg['signkeypw'])

        sign_cmd = 'jarsigner -verbose' \
                + ' -sigalg SHA1withRSA' \
                + ' -digestalg SHA1' \
                + ' -keystore {}'.format(cfg['keystore']) \
                + ' -storepass {}'.format(cfg['keystorepw']) \
                + ' -keypass {}'.format(cfg['signkeypw']) \
                + ' ./{app}-release-unsigned-{ver}.apk {key}'.format(
                    app=cfg['app_name'],
                    ver=cfg['app_version'],
                    key=cfg['signkey'])
                # + ' {p4a}/dists/{dist}/bin/{app}-{ver}-release-unsigned.apk {key}'.format(
                #    p4a=cfg['p4a_path'],
                #    dist=cfg['dist_name'],
                #    app=cfg['app_name'],
                #    ver=cfg['app_version'],
                #    key=cfg['signkey'])


        zipalign_path = ""
        for subdir, dirs, files in os.walk(
                os.path.join(cfg['sdk_path'], 'build-tools')):
            for f in files:
                if f == "zipalign":
                    zipalign_path = os.path.join(subdir, f)
                    break

        # align_cmd = '{zipalign} -v 4 {p4a}/dists/{dist}/bin/{app}-{ver}-release-unsigned.apk {app}-{ver}.apk'.format(
        #    zipalign=zipalign_path, p4a=cfg['p4a_path'], dist=cfg['dist_name'], app=cfg['app_name'], ver=cfg['app_version'])
        align_cmd = '{zipalign} -v 4 {app}-release-unsigned-{ver}.apk {app}-{ver}.apk'.format(
            zipalign=zipalign_path, app=cfg['app_name'], ver=cfg['app_version'])
        os.system(clean_cmd)
        os.system(make_diag_cmd)
        os.system(build_cmd)
        os.system(sign_cmd)
        os.system(align_cmd)

        print("make_diag command was: \n" + make_diag_cmd)
        print("build command was: \n" + build_cmd)
        print("sign command was: \n" + sign_cmd)
        print("align command was: \n" + align_cmd)

        rename_cmd = 'mv '+cfg['app_name']+'__'+cfg['arch']+'-release-unsigned-'+cfg['app_version']+'-.apk '\
                   + cfg['app_name']+'-release-unsigned-'+cfg['app_version']+'.apk '
        os.system(rename_cmd)

    else:
        os.system(make_diag_cmd)
        os.system(build_cmd)
        print("make_diag command was: \n" + make_diag_cmd)
        print("build command was: \n" + build_cmd)

        rename_cmd = 'mv '+cfg['app_name']+'__'+cfg['arch']+'-debug-'+cfg['app_version']+'-.apk '\
                   + cfg['app_name']+'-debug-'+cfg['app_version']+'.apk '
        os.system(rename_cmd)


if __name__ == '__main__':
    arg = sys.argv[1]

    try:
        debug = sys.argv[2]
    except BaseException:
        debug = ""

    try:
        with open("./config/config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
    except BaseException:
        print("Compilation environment is not configured!\nRunning make config automatically for you...")
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
            print("Usage: python deploy.py apk [debug|release]")
    elif arg == 'clean':
        for subdir, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith(".pyo") or f.endswith(".DS_Store"):
                    filepath = os.path.join(subdir, f)
                    os.remove(filepath)
    elif arg == 'clean_apk':
        try:
            os.remove(
                '{path}/{app}-{ver}.apk'.format(
                    path=cfg['mi_dev_path'],
                    app=cfg['app_name'],
                    ver=cfg['app_version']))
            os.remove(
                '{path}/{app}-{ver}-debug.apk'.format(
                    path=cfg['mi_dev_path'],
                    app=cfg['app_name'],
                    ver=cfg['app_version']))
        except BaseException:
            print("APK clean failed.")
    elif arg == 'clean_dist':
        try:
            os.system(
                'rm -rf ' +
                os.path.join(
                    cfg['p4a_path'],
                    'dists',
                    cfg['dist_name']+"*"))
            os.system(
                'rm -rf ' +
                os.path.join(
                    cfg['p4a_path'],
                    'build/aars',
                    cfg['dist_name']))
            os.system(
                'rm -rf ' +
                os.path.join(
                    cfg['p4a_path'],
                    'build/javaclasses',
                    cfg['dist_name']))
            os.system(
                'rm -rf ' +
                os.path.join(
                    cfg['p4a_path'],
                    'build/libs_collections',
                    cfg['dist_name']))
            os.system(
                'rm -rf ' +
                os.path.join(
                    cfg['p4a_path'],
                    'build/python-installs',
                    cfg['dist_name']))
            os.system('p4a clean_dists')
            print("Dist %s successfully cleaned." % cfg['dist_name'])
        except BaseException:
            print("Dist %s clean failed.")
    elif arg == 'clean_all':
        try:
            os.system('p4a clean_all')
            os.system('p4a clean_builds')
            os.system('p4a clean_dists')
            os.system('p4a clean_download_cache')
        except BaseException:
            pass
    elif arg == 'install':
        try:
            # os.system('adb install -r {app}-{ver}.apk'.format(app=cfg['app_name'], ver=cfg['app_version']))
            subprocess.call(
                ['adb install -r {app}-{ver}.apk'.format(app=cfg['app_name'], ver=cfg['app_version'])])
        except BaseException:
            os.system(
                'adb install -r {app}-{ver}-debug.apk'.format(
                    app=cfg['app_name'],
                    ver=cfg['app_version']))
    elif arg == 'update':
        try:
            plg = sys.argv[2]
            desktop_path = "./internal_app/" + plg
            if os.path.isdir(desktop_path):
                os.system(
                    'adb shell "rm -r /sdcard/mobileinsight/plugins/{plugin}"'.format(plugin=plg))
                os.system(
                    'adb push ./internal_app/{plugin} /sdcard/mobileinsight/plugins/{plugin}'.format(plugin=plg))
            else:
                print("Sorry, the plugin {plugin} does not exist".format(plugin=plg))
        except BaseException:
            print("Sorry, the plugin {plugin} does not exist".format(plugin=plg))
