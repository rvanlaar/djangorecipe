from random import choice
import os
import logging
import sys

from zc.buildout import UserError
import zc.recipe.egg

from djangorecipe.boilerplate import script_template


class Recipe(object):
    def __init__(self, buildout, name, options):
        # Deprecations
        if 'version' in options:
            raise UserError('The version option is deprecated. '
                            'Read about the change on '
                            'http://pypi.python.org/pypi/djangorecipe/0.99')
        if 'projectegg' in options:
            self.log.warn("The projectegg option is deprecated. "
                          "See the changelog for 2.0 at "
                          "http://pypi.python.org/pypi/djangorecipe/2.0")

        # TODO: Check if dir exists, otherwise hint at bin/django

        self.log = logging.getLogger(name)
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        self.buildout, self.name, self.options = buildout, name, options
        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'], name)
        options['bin-directory'] = buildout['buildout']['bin-directory']

        options.setdefault('project', 'project')
        options.setdefault('settings', 'development')

        options.setdefault('urlconf', options['project'] + '.urls')
        options.setdefault(
            'media_root',
            "os.path.join(os.path.dirname(__file__), 'media')")
        # Set this so the rest of the recipe can expect the values to be
        # there. We need to make sure that both pythonpath and extra-paths are
        # set for BBB.
        if 'extra-paths' in options:
            options['pythonpath'] = options['extra-paths']
        else:
            options.setdefault('extra-paths', options.get('pythonpath', ''))

        options.setdefault('initialization', '')
        options.setdefault('deploy-script-extra', '')

        # mod_wsgi support script
        options.setdefault('wsgi', 'false')
        options.setdefault('wsgilog', '')
        options.setdefault('logfile', '')

        # respect relative-paths (from zc.recipe.egg)
        relative_paths = options.get(
            'relative-paths', buildout['buildout'].get('relative-paths',
                                                       'false'))
        if relative_paths == 'true':
            options['buildout-directory'] = buildout['buildout']['directory']
            self._relative_paths = options['buildout-directory']
        else:
            self._relative_paths = ''
            assert relative_paths == 'false'

    def install(self):
        extra_paths = self.get_extra_paths()
        requirements, ws = self.egg.working_set(['djangorecipe'])

        script_paths = []
        # Create the Django management script
        script_paths.extend(self.create_manage_script(extra_paths, ws))

        # Create the test runner
        script_paths.extend(self.create_test_runner(extra_paths, ws))

        # Make the wsgi and fastcgi scripts if enabled
        script_paths.extend(self.make_scripts(extra_paths, ws))

        return script_paths

    def create_manage_script(self, extra_paths, ws):
        settings = self.get_settings()
        return zc.buildout.easy_install.scripts(
            [(self.options.get('control-script', self.name),
              'djangorecipe.manage', 'main')],
            ws, sys.executable, self.options['bin-directory'],
            extra_paths=extra_paths,
            relative_paths=self._relative_paths,
            arguments="'%s'" % settings,
            initialization=self.options['initialization'])

    def create_test_runner(self, extra_paths, working_set):
        settings = self.get_settings()
        apps = self.options.get('test', '').split()
        # Only create the testrunner if the user requests it
        if apps:
            return zc.buildout.easy_install.scripts(
                [(self.options.get('testrunner', 'test'),
                  'djangorecipe.test', 'main')],
                working_set, sys.executable,
                self.options['bin-directory'],
                extra_paths=extra_paths,
                relative_paths=self._relative_paths,
                arguments="'%s', %s" % (
                    settings, ', '.join(["'%s'" % app for app in apps])),
                initialization=self.options['initialization'])
        else:
            return []

    def make_scripts(self, extra_paths, ws):
        scripts = []
        _script_template = zc.buildout.easy_install.script_template
        protocol = 'wsgi'
        settings = self.get_settings()
        if 'deploy_script_extra' in self.options:
            # Renamed between 1.9 and 1.10
            raise ValueError(
                "'deploy_script_extra' option found (with underscores). " +
                "This has been renamed to 'deploy-script-extra'.")
        zc.buildout.easy_install.script_template = (
            zc.buildout.easy_install.script_header +
            script_template[protocol] +
            self.options['deploy-script-extra']
        )
        if self.options.get(protocol, '').lower() == 'true':
            scripts.extend(
                zc.buildout.easy_install.scripts(
                    [(self.options.get('wsgi-script') or
                      '%s.%s' % (self.options.get('control-script',
                                                  self.name),
                                 protocol),
                      'djangorecipe.%s' % protocol, 'main')],
                    ws,
                    sys.executable,
                    self.options['bin-directory'],
                    extra_paths=extra_paths,
                    relative_paths=self._relative_paths,
                    arguments="'%s', logfile='%s'" % (
                        settings, self.options.get('logfile')),
                    initialization=self.options['initialization'],
                ))
        zc.buildout.easy_install.script_template = _script_template
        return scripts

    def get_extra_paths(self):
        extra_paths = [self.buildout['buildout']['directory']]

        # Add libraries found by a site .pth files to our extra-paths.
        if 'pth-files' in self.options:
            import site
            for pth_file in self.options['pth-files'].splitlines():
                pth_libs = site.addsitedir(pth_file, set())
                if not pth_libs:
                    self.log.warning(
                        "No site *.pth libraries found for pth_file=%s",
                        pth_file)
                else:
                    self.log.info("Adding *.pth libraries=%s", pth_libs)
                    self.options['extra-paths'] += '\n' + '\n'.join(pth_libs)

        pythonpath = [p.replace('/', os.path.sep) for p in
                      self.options['extra-paths'].splitlines() if p.strip()]

        extra_paths.extend(pythonpath)
        return extra_paths

    def update(self):
        extra_paths = self.get_extra_paths()
        requirements, ws = self.egg.working_set(['djangorecipe'])
        # Create the Django management script
        self.create_manage_script(extra_paths, ws)

        # Create the test runner
        self.create_test_runner(extra_paths, ws)

        # Make the wsgi and fastcgi scripts if enabled
        self.make_scripts(extra_paths, ws)

    def create_file(self, file, template, options):
        if os.path.exists(file):
            return

        f = open(file, 'w')
        f.write(template % options)
        f.close()

    def generate_secret(self):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        return ''.join([choice(chars) for i in range(50)])

    def get_settings(self):
        settings = '%s.%s' % (self.options['project'], self.options['settings'])
        settings = self.options.get('dotted-settings-path', settings)
        return settings
