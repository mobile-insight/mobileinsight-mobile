from pythonforandroid.toolchain import Recipe, shprint, current_directory
from pythonforandroid.logger import info, debug, shprint, warning
from os.path import exists, join, isdir, split
import sh
import glob

class MobileInsightRecipe(Recipe):

    mi_git            = 'https://wing1.cs.ucla.edu/gitlab/root/automator.git'
    mi_branch         = 'master'
    version           = '2.1'
    toolchain_version = 4.8          # default GCC toolchain version we try to use
    depends           = ['python2']  # any other recipe names that must be built before this one

    def get_newest_toolchain(self, arch):

        # warning("get_newest_toolchain(self, arch), toolchain prefix = {}".format(toolchain_prefix))
        # [WARNING]: get_newest_toolchain(self, arch), toolchain prefix = arm-linux-androideabi

        toolchain_versions = []
        toolchain_prefix   = arch.toolchain_prefix
        toolchain_path     = join(self.ctx.ndk_dir, 'toolchains')
        if isdir(toolchain_path):
            toolchain_contents = glob.glob('{}/{}-*'.format(toolchain_path,
                                                            toolchain_prefix))
            toolchain_versions = [split(path)[-1][len(toolchain_prefix) + 1:]
                                  for path in toolchain_contents]
        else:
            warning('Could not find toolchain subdirectory!')
        toolchain_versions.sort()

        toolchain_versions_gcc = []
        for toolchain_version in toolchain_versions:
            if toolchain_version[0].isdigit():
                toolchain_versions_gcc.append(toolchain_version) # GCC toolchains begin with a number

        if toolchain_versions:
            toolchain_version = toolchain_versions_gcc[-1] # the latest gcc toolchain
        else:
            warning('Could not find any toolchain for {}!'.format(toolchain_prefix))

        self.toolchain_version = toolchain_version

    def get_recipe_env(self, arch):
        env = super(MobileInsightRecipe, self).get_recipe_env(arch)

        warning("get_recipe_env(self, arch), use toolchain version = {toolchain_version}".format(
            toolchain_version   = self.toolchain_version))
        env['CFLAGS'] += ' -fPIC'
        env['CFLAGS'] += ' -I{ndk_dir}/sources/cxx-stl/gnu-libstdc++/{toolchain_version}/include'.format(
            ndk_dir             = self.ctx.ndk_dir,
            toolchain_version   = self.toolchain_version)
        env['CFLAGS'] += ' -I{ndk_dir}/sources/cxx-stl/gnu-libstdc++/{toolchain_version}/libs/{arch}/include'.format(
            ndk_dir             = self.ctx.ndk_dir,
            toolchain_version   = self.toolchain_version,
            arch                = arch)
        # env['CXXFLAGS'] += ' -Os -fPIC -fvisibility=default'
        # env['CXXFLAGS'] += ' -I{ndk_dir}/sources/cxx-stl/gnu-libstdc++/{toolchain_version}/include'.format(
        #     ndk_dir             = self.ctx.ndk_dir,
        #     toolchain_version   = self.toolchain_version)
        # env['CXXFLAGS'] += ' -I{ndk_dir}/sources/cxx-stl/gnu-libstdc++/{toolchain_version}/libs/{arch}/include'.format(
        #     ndk_dir             = self.ctx.ndk_dir,
        #     toolchain_version   = self.toolchain_version,
        #     arch                = arch)
        env['LDFLAGS'] += ' -L{ndk_dir}/sources/cxx-stl/gnu-libstdc++/{toolchain_version}/libs/{arch}'.format(
            ndk_dir             = self.ctx.ndk_dir,
            toolchain_version   = self.toolchain_version,
            arch                = arch)
        env['LDFLAGS'] += ' -shared'
        env['LDFLAGS'] += ' -lgnustl_shared'
        env['STRIP']    = str.split(env['STRIP'])[0]

        # warning("I am printing the env now")
        # shprint(sh.echo, '$PATH', _env=env)
        # warning("I am printing self.ctx.ndk-dir = {}".format(self.ctx.ndk_dir))
        # warning("I am printing self.ctx.build_dir = {}".format(self.ctx.build_dir))
        # warning("I am printing self.ctx.libs_dir = {}".format(self.ctx.libs_dir))
        # warning("I am printing self.ctx.bootstrap.build_dir = {}".format(self.ctx.bootstrap.build_dir))
        # warning("I am printing self.ctx = {}".format(str(self.ctx)))
        return env


    def prebuild_arch(self, arch):
        super(MobileInsightRecipe, self).prebuild_arch(arch)

        build_dir = self.get_build_dir(arch.arch)
        tmp_dir = join(build_dir, 'mi_tmp')
        info("clean old MI2 sources at {}".format(build_dir))
        try:
            shprint(sh.rm, '-r',
                    build_dir,
                    _tail     = 20,
                    _critical = True)
        except:
            pass

        info("clone MobileInsight sources from {}".format(self.mi_git))
        shprint(sh.git,
                'clone', '-b',
                self.mi_branch,
                '--depth=1',
                self.mi_git,
                tmp_dir,
                _tail     = 20,
                _critical = True)
        
        shprint(sh.mv,
                join(tmp_dir, 'mobile_insight'),
                build_dir,
                _tail     = 20,
                _critical = True)
        shprint(sh.mv,
                join(tmp_dir, 'dm_collector_c'),
                build_dir,
                _tail     = 20,
                _critical = True)

        # remove unnecessary codes
        shprint(sh.rm, '-r', tmp_dir,
                _tail     = 20,
                _critical = True)

        self.get_newest_toolchain(arch)

        warning("MI2 -- Should also clean and remove unnecessary codes, skipping now.")
        # remove unnecessary code
        # sed -i '' is using Mac OS X sed syntax
        # TODO
        # sed -i'' is using GNU version sed syntax
        # shprint(sh.grep, '-v', '"### P4A.*"',
        #         join(build_dir, 'mobile_insight/monitor/__init__.py'),
        #         '>',
        #         join(build_dir, 'mobile_insight/monitor/__init__.py.bak'),
        #         _tail     = 20,
        #         _critical = True)
        # shprint(sh.mv,
        #         join(build_dir, 'mobile_insight/monitor/__init__.py.bak'),
        #         join(build_dir, 'mobile_insight/monitor/__init__.py'),
        #         _tail     = 20,
        #         _critical = True)

        # shprint(sh.grep, '-v', '"### P4A.*"',
        #         join(build_dir, 'mobile_insight/monitor/dm_collector/__init__.py'),
        #         '>',
        #         join(build_dir, 'mobile_insight/monitor/dm_collector/__init__.py.bak'),
        #         _tail     = 20,
        #         _critical = True)
        # shprint(sh.mv,
        #         join(build_dir, 'mobile_insight/monitor/dm_collector/__init__.py.bak'),
        #         join(build_dir, 'mobile_insight/monitor/dm_collector/__init__.py'),
        #         _tail     = 20,
        #         _critical = True)
        
        # shprint(sh.grep, '-v', '"### P4A.*"',
        #         join(build_dir, 'mobile_insight/monitor/dm_collector/dm_endec/ws_dissector.py'),
        #         '>',
        #         join(build_dir, 'mobile_insight/monitor/dm_collector/dm_endec/ws_dissector.py.bak'),
        #         _tail     = 20,
        #         _critical = True)
        # shprint(sh.mv,
        #         join(build_dir, 'mobile_insight/monitor/dm_collector/dm_endec/ws_dissector.py.bak'),
        #         join(build_dir, 'mobile_insight/monitor/dm_collector/dm_endec/ws_dissector.py'),
        #         _tail     = 20,
        #         _critical = True)

        # shprint(sh.rm,
        #         join(build_dir, 'mobile_insight/monitor/dm_collector/dm_collector.py'),
        #         _tail     = 20,
        #         _critical = True)


    def build_arch(self, arch):
        super(MobileInsightRecipe, self).build_arch(arch)

        env = self.get_recipe_env(arch)
        # self.build_cython_components(arch)

        with current_directory(self.get_build_dir(arch.arch)):
            hostpython = sh.Command(self.ctx.hostpython)
            app_mk     = join(self.get_build_dir(arch.arch), 'Application.mk')
            app_setup  = join(self.get_build_dir(arch.arch), 'setup.py')

            if not exists(app_mk):
                shprint(sh.cp, join(self.get_recipe_dir(), 'Application.mk'), app_mk)
            if not exists(app_setup):
                shprint(sh.cp, join(self.get_recipe_dir(), 'setup.py'), app_setup)

            shprint(hostpython, 'setup.py', 'build_ext', '-v', _env = env, _tail = 10, _critical = True)
            shprint(hostpython, 'setup.py', 'install',  '-O2', _env = env, _tail = 10, _critical = True)

            build_lib = glob.glob('./build/lib*')
            assert len(build_lib) == 1
            warning('MI2 -- stripping mobileinsight')

            # shprint(sh.find, build_lib[0], '-name', '*.o', '-exec', env['STRIP'], '{}', ';', _tail = 20, _critical = True)
            shprint(sh.find, build_lib[0], '-name', '*.so', '-exec', env['STRIP'], '{}', ';', _tail = 20, _critical = True)

        try:
            warning('copying GNU STL shared lib to {libs_dir}/{arch}'.format(
                    libs_dir          = self.ctx.libs_dir,
                    arch              = arch))
            shprint(sh.cp,
                '{ndk_dir}/sources/cxx-stl/gnu-libstdc++/{toolchain_version}/libs/{arch}/libgnustl_shared.so'.format(
                    ndk_dir           = self.ctx.ndk_dir,
                    toolchain_version = self.toolchain_version,
                    arch              = arch),
                '{libs_dir}/{arch}'.format(
                    libs_dir          = self.ctx.libs_dir,
                    arch              = arch))
        except:
            warning('failed to copy GNU STL shared lib!!')

    def build_cython_components(self, arch):
        env = self.get_recipe_env(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            info('hostpython is ' + self.ctx.hostpython)
            hostpython = sh.Command(self.ctx.hostpython)

            app_mk = join(self.get_build_dir(arch.arch), 'Application.mk')
            if not exists(app_mk):
                shprint(sh.cp, join(self.get_recipe_dir(), 'Application.mk'), app_mk)
            app_setup = join(self.get_build_dir(arch.arch), 'setup.py')
            if not exists(app_setup):
                shprint(sh.cp, join(self.get_recipe_dir(), 'setup.py'), app_setup)

            # This first attempt *will* fail, because cython isn't
            # installed in the hostpython
            try:
                shprint(hostpython, 'setup.py', 'build_ext', _env=env)
            except sh.ErrorReturnCode_1:
                pass

            # ...so we manually run cython from the user's system
            shprint(sh.find, self.get_build_dir('armeabi'), '-iname', '*.pyx', '-exec',
                    self.ctx.cython, '{}', ';', _env=env)

            # now cython has already been run so the build works
            shprint(hostpython, 'setup.py', 'build_ext', '-v', _env=env)

            # stripping debug symbols lowers the file size a lot
            build_lib = glob.glob('./build/lib*')
            shprint(sh.find, build_lib[0], '-name', '*.o', '-exec',
                    env['STRIP'], '{}', ';', _env=env)

    def postbuild_arch(self, arch):
        super(MobileInsightRecipe, self).postbuild_arch(arch)

        # TODO
        warning('Should remove mobileinsight build tools etc. here, but skipping for now')
        #     try rm -rf $BUILD_PATH/python-install/lib/python*/site-packages/mobile_insight/tools

recipe = MobileInsightRecipe()
