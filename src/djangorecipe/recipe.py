import os
import logging
import sys

from zc.buildout import UserError
import zc.recipe.egg

from djangorecipe.boilerplate import WSGI_TEMPLATE


class Recipe(object):
    def __init__(self, buildout, name, options):
        self.log = logging.getLogger(name)

        # Deprecations
        if 'version' in options:
            raise UserError('The version option is deprecated. '
                            'Read about the change on '
                            'http://pypi.python.org/pypi/djangorecipe/0.99')
        if 'wsgilog' in options:
            raise UserError('The wsgilog option is deprecated. '
                            'Read about the change on '
                            'http://pypi.python.org/pypi/djangorecipe/2.0')
        if 'projectegg' in options:
            raise UserError("The projectegg option is deprecated. "
                            "See the changelog for 2.0 at "
                            "http://pypi.python.org/pypi/djangorecipe/2.0")
        if 'deploy_script_extra' in options:
            # Renamed between 1.9 and 1.10
            raise UserError(
                "'deploy_script_extra' option found (with underscores). "
                "This has been renamed to 'deploy-script-extra'.")

        # Generic initialization.
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)
        self.buildout, self.name, self.options = buildout, name, options
        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'], name)
        options['bin-directory'] = buildout['buildout']['bin-directory']

        # Option defaults.
        options.setdefault('project', 'project')
        options.setdefault('settings', 'development')
        options.setdefault('extra-paths', '')
        options.setdefault('initialization', '')
        options.setdefault('deploy-script-extra', '')

        # mod_wsgi support script
        options.setdefault('wsgi', 'false')
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
        if self.options['project'] not in os.listdir(
                self.buildout['buildout']['directory']):
            # Only warn for this upon install, not on update.
            self.log.warn(
                "There's no directory named after our project. "
                "Probably you want to run 'bin/django startproject %s'",
                self.options['project'])

        extra_paths = self.get_extra_paths()
        ws = self.egg.working_set(['djangorecipe'])[1]
        # ^^^ working_set returns (requirements, ws)

        script_paths = []
        # Create the Django management script
        script_paths.extend(self.create_manage_script(extra_paths, ws))

        # Create the test runner
        script_paths.extend(self.create_test_runner(extra_paths, ws))

        # Make the wsgi script if enabled
        script_paths.extend(self.make_wsgi_script(extra_paths, ws))

        return script_paths

    def create_manage_script(self, extra_paths, ws):
        settings = self.get_settings()
        return zc.buildout.easy_install.scripts(
            [(self.options.get('control-script', self.name),
              'djangorecipe.binscripts', 'manage')],
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
                  'djangorecipe.binscripts', 'test')],
                working_set, sys.executable,
                self.options['bin-directory'],
                extra_paths=extra_paths,
                relative_paths=self._relative_paths,
                arguments="'%s', %s" % (
                    settings, ', '.join(["'%s'" % app for app in apps])),
                initialization=self.options['initialization'])
        else:
            return []

    def make_wsgi_script(self, extra_paths, ws):
        scripts = []
        _script_template = zc.buildout.easy_install.script_template
        settings = self.get_settings()
        zc.buildout.easy_install.script_template = (
            zc.buildout.easy_install.script_header +
            WSGI_TEMPLATE +
            self.options['deploy-script-extra']
        )
        if self.options.get('wsgi', '').lower() == 'true':
            scripts.extend(
                zc.buildout.easy_install.scripts(
                    [(self.options.get('wsgi-script') or
                      '%s.%s' % (self.options.get('control-script',
                                                  self.name),
                                 'wsgi'),
                      'djangorecipe.binscripts', 'wsgi')],
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
        pythonpath = [p.replace('/', os.path.sep) for p in
                      self.options['extra-paths'].splitlines() if p.strip()]
        extra_paths.extend(pythonpath)
        return extra_paths

    def update(self):
        extra_paths = self.get_extra_paths()
        ws = self.egg.working_set(['djangorecipe'])[1]
        # ^^^ working_set returns (requirements, ws)

        self.create_manage_script(extra_paths, ws)
        self.create_test_runner(extra_paths, ws)
        self.make_wsgi_script(extra_paths, ws)

    def create_file(self, filename, template, options):
        if os.path.exists(filename):
            return
        f = open(filename, 'w')
        f.write(template % options)
        f.close()

    def get_settings(self):
        settings = '%s.%s' % (self.options['project'], self.options['settings'])
        settings = self.options.get('dotted-settings-path', settings)
        return settings
