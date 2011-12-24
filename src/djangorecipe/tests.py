import unittest
import tempfile
import os
import sys
import shutil

import mock

from djangorecipe.recipe import Recipe


class TestRecipe(unittest.TestCase):

    def setUp(self):
        # Create a directory for our buildout files created by the recipe
        self.buildout_dir = tempfile.mkdtemp('djangorecipe')

        self.bin_dir = os.path.join(self.buildout_dir, 'bin')
        self.develop_eggs_dir = os.path.join(self.buildout_dir,
                                             'develop-eggs')
        self.eggs_dir = os.path.join(self.buildout_dir, 'eggs')
        self.parts_dir = os.path.join(self.buildout_dir, 'parts')

        # We need to create the bin dir since the recipe should be able to
        # expect it exists
        os.mkdir(self.bin_dir)

        self.recipe = Recipe({
                'buildout': {
                    'eggs-directory': self.eggs_dir,
                    'develop-eggs-directory': self.develop_eggs_dir,
                    'python': 'python-version',
                    'bin-directory': self.bin_dir,
                    'parts-directory': self.parts_dir,
                    'directory': self.buildout_dir,
                    'find-links': '',
                    'allow-hosts': '',
                    },
                'python-version': {'executable': sys.executable}},
                             'django',
                             {'recipe': 'djangorecipe'})

    def tearDown(self):
        # Remove our test dir
        shutil.rmtree(self.buildout_dir)

    def test_consistent_options(self):
        # Buildout is pretty clever in detecting changing options. If
        # the recipe modifies it's options during initialisation it
        # will store this to determine wheter it needs to update or do
        # a uninstall & install. We need to make sure that we normally
        # do not trigger this. That means running the recipe with the
        # same options should give us the same results.
        self.assertEqual(*[
                Recipe({'buildout': {
                            'eggs-directory': self.eggs_dir,
                            'develop-eggs-directory': self.develop_eggs_dir,
                            'python': 'python-version',
                            'bin-directory': self.bin_dir,
                            'parts-directory': self.parts_dir,
                            'directory': self.buildout_dir,
                            'find-links': '',
                            'allow-hosts':'',
                            },
                        'python-version': {'executable': sys.executable}},
                       'django',
                       {'recipe': 'djangorecipe'}).options.copy()
                for i in range(2)])

    def test_create_file(self):
        # The create file helper should create a file at a certain
        # location unless it already exists. We will need a
        # non-existing file first.
        f, name = tempfile.mkstemp()
        # To show the function in action we need to delete the file
        # before testing.
        os.remove(name)
        # The method accepts a template argument which it will use
        # with the options argument for string substitution.
        self.recipe.create_file(name, 'Spam %s', 'eggs')
        # Let's check the contents of the file
        self.assertEqual(open(name).read(), 'Spam eggs')
        # If we try to write it again it will just ignore our request
        self.recipe.create_file(name, 'Spam spam spam %s', 'eggs')
        # The content of the file should therefore be the same
        self.assertEqual(open(name).read(), 'Spam eggs')
        # Now remove our temp file
        os.remove(name)

    def test_generate_secret(self):
        # To create a basic skeleton the recipe also generates a
        # random secret for the settings file. Since it should very
        # unlikely that it will generate the same key a few times in a
        # row we will test it with letting it generate a few keys.
        self.assert_(len(set(
                    [self.recipe.generate_secret() for i in range(10)])) > 1)

    def test_make_protocol_scripts(self):
        # To ease deployment a WSGI script can be generated. The
        # script adds any paths from the `extra_paths` option to the
        # Python path.
        self.recipe.options['wsgi'] = 'true'
        self.recipe.options['fcgi'] = 'true'
        self.recipe.make_scripts([], [])
        # This should have created a script in the bin dir
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        self.assert_(os.path.exists(wsgi_script))
        # The contents should list our paths
        contents = open(wsgi_script).read()
        # It should also have a reference to our settings module
        self.assert_('project.development' in contents)
        # and a line which set's up the WSGI app
        self.assert_("application = "
                     "djangorecipe.wsgi.main('project.development', "
                     "logfile='')"
                     in contents)
        self.assert_("class logger(object)" not in contents)

        # Another deployment options is FCGI. The recipe supports an option to
        # automatically create the required script.
        fcgi_script = os.path.join(self.bin_dir, 'django.fcgi')
        self.assert_(os.path.exists(fcgi_script))
        # The contents should list our paths
        contents = open(fcgi_script).read()
        # It should also have a reference to our settings module
        self.assert_('project.development' in contents)
        # and a line which set's up the WSGI app
        self.assert_("djangorecipe.fcgi.main('project.development', "
                     "logfile='')"
                     in contents)
        self.assert_("class logger(object)" not in contents)

        self.recipe.options['logfile'] = '/foo'
        self.recipe.make_scripts([], [])
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        contents = open(wsgi_script).read()
        self.assert_("logfile='/foo'" in contents)

        self.recipe.options['logfile'] = '/foo'
        self.recipe.make_scripts([], [])
        fcgi_script = os.path.join(self.bin_dir, 'django.fcgi')
        contents = open(fcgi_script).read()
        self.assert_("logfile='/foo'" in contents)

    @mock.patch('zc.buildout.easy_install.scripts')
    def test_make_protocol_scripts_return_value(self, scripts):
        # The return value of make scripts lists the generated scripts.
        self.recipe.options['wsgi'] = 'true'
        self.recipe.options['fcgi'] = 'true'
        scripts.return_value = ['some-path']
        self.assertEqual(self.recipe.make_scripts([], []),
                         ['some-path', 'some-path'])

    def test_create_project(self):
        # If a project does not exist already the recipe will create
        # one.
        project_dir = os.path.join(self.buildout_dir, 'project')
        self.recipe.create_project(project_dir)
        # This should have create a project directory
        self.assert_(os.path.exists(project_dir))
        # With this directory we should have __init__.py to make it a
        # package
        self.assert_(
            os.path.exists(os.path.join(project_dir, '__init__.py')))
        # There should also be a urls.py
        self.assert_(
            os.path.exists(os.path.join(project_dir, 'urls.py')))
        # To make it easier to start using this project both a media
        # and a templates folder are created
        self.assert_(
            os.path.exists(os.path.join(project_dir, 'media')))
        self.assert_(
            os.path.exists(os.path.join(project_dir, 'templates')))
        # The project is ready to go since the recipe has generated a
        # base settings, development and production file
        for f in ('settings.py', 'development.py', 'production.py'):
            self.assert_(
                os.path.exists(os.path.join(project_dir, f)))

    def test_create_test_runner(self):
        # An executable script can be generated which will make it
        # possible to execute the Django test runner. This options
        # only works if we specify one or apps to test.
        testrunner = os.path.join(self.bin_dir, 'test')

        # This first argument sets extra_paths, we will use this to
        # make sure the script can find this recipe
        recipe_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))

        # First we will show it does nothing by default
        self.recipe.create_test_runner([recipe_dir], [])
        self.failIf(os.path.exists(testrunner))

        # When we specify an app to test it should create the the
        # testrunner
        self.recipe.options['test'] = 'knight'
        self.recipe.create_test_runner([recipe_dir], [])
        self.assert_(os.path.exists(testrunner))

    def test_create_manage_script(self):
        # This buildout recipe creates a alternative for the standard
        # manage.py script. It has all the same functionality as the
        # original one but it sits in the bin dir instead of within
        # the project.
        manage = os.path.join(self.bin_dir, 'django')
        self.recipe.create_manage_script([], [])
        self.assert_(os.path.exists(manage))

    def test_create_manage_script_projectegg(self):
        # When a projectegg is specified, then the egg specified
        # should get used as the project file.
        manage = os.path.join(self.bin_dir, 'django')
        self.recipe.options['projectegg'] = 'spameggs'
        self.recipe.create_manage_script([], [])
        self.assert_(os.path.exists(manage))
        # Check that we have 'spameggs' as the project
        self.assert_("djangorecipe.manage.main('spameggs.development')"
                     in open(manage).read())

    @mock.patch('os.path.exists')
    @mock.patch('zc.recipe.egg.egg.Scripts.working_set')
    @mock.patch('zc.buildout.easy_install.scripts')
    @mock.patch('djangorecipe.recipe.Recipe.create_manage_script')
    @mock.patch('djangorecipe.recipe.Recipe.create_test_runner')
    def test_extra_paths(self, testrunner, manage, scripts,
                         working_set, path_exists):

        # The recipe allows extra-paths to be specified. It uses these to
        # extend the Python path within it's generated scripts.
        self.recipe.options['version'] = '1.0'
        self.recipe.options['extra-paths'] = 'somepackage\nanotherpackage'
        path_exists.return_value = True
        working_set.return_value = (None, [])
        manage.return_value = []
        scripts.return_value = []
        testrunner.return_value = []
        self.recipe.install()
        self.assertEqual(manage.call_args[0][0][-2:],
                         ['somepackage', 'anotherpackage'])

    @mock.patch('os.path.exists')
    @mock.patch('zc.recipe.egg.egg.Scripts.working_set')
    @mock.patch('zc.buildout.easy_install.scripts')
    @mock.patch('djangorecipe.recipe.Recipe.create_manage_script')
    @mock.patch('djangorecipe.recipe.Recipe.create_test_runner')
    @mock.patch('site.addsitedir')
    def test_pth_files(self, addsitedir, testrunner, manage,
                       scripts, working_set, path_exists,):

        # When a pth-files option is set the recipe will use that to add more
        # paths to extra-paths.
        self.recipe.options['version'] = '1.0'
        path_exists.return_value = True
        working_set.return_value = (None, [])
        scripts.return_value = []
        manage.return_value = []
        testrunner.return_value = []

        # The mock values needed to demonstrate the pth-files option.
        addsitedir.return_value = ['extra', 'dirs']
        self.recipe.options['pth-files'] = 'somedir'

        self.recipe.install()
        self.assertEqual(addsitedir.call_args, (('somedir', set([])), {}))
        # The extra-paths option has been extended.
        self.assertEqual(self.recipe.options['extra-paths'], '\nextra\ndirs')

    def test_create_wsgi_script_projectegg(self):
        # When a projectegg is specified, then the egg specified
        # should get used as the project in the wsgi script.
        wsgi = os.path.join(self.bin_dir, 'django.wsgi')
        recipe_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))
        self.recipe.options['projectegg'] = 'spameggs'
        self.recipe.options['wsgi'] = 'true'
        self.recipe.make_scripts([recipe_dir], [])
        self.assert_(os.path.exists(wsgi))
        # Check that we have 'spameggs' as the project
        self.assert_('spameggs.development' in open(wsgi).read())

    def test_settings_option(self):
        # The settings option can be used to specify the settings file
        # for Django to use. By default it uses `development`.
        self.assertEqual(self.recipe.options['settings'], 'development')
        # When we change it an generate a manage script it will use
        # this var.
        self.recipe.options['settings'] = 'spameggs'
        self.recipe.create_manage_script([], [])
        manage = os.path.join(self.bin_dir, 'django')
        self.assert_("djangorecipe.manage.main('project.spameggs')"
                     in open(manage).read())

    def test_python_option(self):
        # The python option makes it possible to specify a specific Python
        # executable which is to be used for the generated scripts.
        recipe = Recipe({
                'buildout': {
                    'eggs-directory': self.eggs_dir,
                    'develop-eggs-directory': self.develop_eggs_dir,
                    'python': 'python-version',
                    'bin-directory': self.bin_dir,
                    'parts-directory': self.parts_dir,
                    'directory': self.buildout_dir,
                    'find-links': '',
                    'allow-hosts': '',
                    },
                'python-version': {'executable': '/python4k'}},
                        'django',
                        {'recipe': 'djangorecipe',
                         'wsgi': 'true'})
        recipe.make_scripts([], [])
        # This should have created a script in the bin dir
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        self.assertEqual(open(wsgi_script).readlines()[0], '#!/python4k\n')
        # Changeing the option for only the part will change the used Python
        # version.
        recipe = Recipe({
                'buildout': {'eggs-directory': self.eggs_dir,
                             'develop-eggs-directory': self.develop_eggs_dir,
                             'python': 'python-version',
                             'bin-directory': self.bin_dir,
                             'parts-directory': self.parts_dir,
                             'directory': self.buildout_dir,
                             'find-links': '',
                             'allow-hosts': '',
                             },
                'python-version': {'executable': '/python4k'},
                'py5k': {'executable': '/python5k'}},
                        'django',
                        {'recipe': 'djangorecipe',
                         'python': 'py5k', 'wsgi': 'true'})
        recipe.make_scripts([], [])
        self.assertEqual(open(wsgi_script).readlines()[0], '#!/python5k\n')

    def test_boilerplate_newest(self):
        """Test the default boilerplate."""

        project_dir = os.path.join(self.buildout_dir, 'project')

        secret = '$55upfci7a#gi@&e9o1-hb*k+f$3+(&b$j=cn67h#22*0%-bj0'
        self.recipe.generate_secret = lambda: secret

        self.recipe.create_project(project_dir)
        settings = open(os.path.join(project_dir, 'settings.py')).read()
        settings_dict = {'project': self.recipe.options['project'],
                         'secret': secret,
                         'urlconf': self.recipe.options['urlconf'],
                         }
        from djangorecipe.boilerplate import versions
        self.assertEquals(versions['Newest']['settings'] % settings_dict,
                          settings)

    def test_boilerplate_1_2(self):
        """Test the boilerplate for django 1.2."""

        recipe = Recipe({
                'buildout': {'eggs-directory': self.eggs_dir,
                             'develop-eggs-directory': self.develop_eggs_dir,
                             'python': 'python-version',
                             'bin-directory': self.bin_dir,
                             'parts-directory': self.parts_dir,
                             'directory': self.buildout_dir,
                             'find-links': '',
                             'allow-hosts': '',
                             'versions': 'versions',
                             },
                'versions': {'django': '1.2.5'},
                'python-version': {'executable': '/python4k'},
                'py5k': {'executable': '/python5k'}},
                        'django',
                        {'recipe': 'djangorecipe',
                         'python': 'py5k', 'wsgi': 'true'})

        secret = '$55upfci7a#gi@&e9o1-hb*k+f$3+(&b$j=cn67h#22*0%-bj0'
        recipe.generate_secret = lambda: secret

        project_dir = os.path.join(self.buildout_dir, 'project')
        recipe.create_project(project_dir)
        settings = open(os.path.join(project_dir, 'settings.py')).read()
        settings_dict = {'project': self.recipe.options['project'],
                         'secret': secret,
                         'urlconf': self.recipe.options['urlconf'],
                         }
        from djangorecipe.boilerplate import versions
        self.assertEquals(versions['1.2']['settings'] % settings_dict,
                          settings)

    def test_versions_deprecation(self):
        from zc.buildout import UserError
        options = {'recipe': 'djangorecipe',
                   'version': 'trunk',
                   'python': 'py5k', 'wsgi': 'true'}
        self.assertRaises(UserError, Recipe, *('buildout', 'test', options))


class ScriptTestCase(unittest.TestCase):

    def setUp(self):
        # We will also need to fake the settings file's module
        self.settings = mock.sentinel.Settings
        sys.modules['cheeseshop'] = mock.sentinel.CheeseShop
        sys.modules['cheeseshop.development'] = self.settings
        sys.modules['cheeseshop'].development = self.settings

    def tearDown(self):
        # We will clear out sys.modules again to clean up
        for m in ['cheeseshop', 'cheeseshop.development']:
            del sys.modules[m]


class TestTestScript(ScriptTestCase):

    @mock.patch('django.core.management.execute_manager')
    def test_script(self, execute_manager):
        # The test script should execute the standard Django test
        # command with any apps given as its arguments.
        from djangorecipe import test
        test.main('cheeseshop.development',  'spamm', 'eggs')
        # We only care about the arguments given to execute_manager
        self.assertEqual(execute_manager.call_args[1],
                         {'argv': ['test', 'test', 'spamm', 'eggs']})

    @mock.patch('django.core.management.execute_manager')
    def test_deeply_nested_settings(self, execute_manager):
        # Settings files can be more than two levels deep. We need to
        # make sure the test script can properly import those. To
        # demonstrate this we need to add another level to our
        # sys.modules entries.
        settings = mock.sentinel.SettingsModule
        nce = mock.sentinel.NCE
        nce.development = settings
        sys.modules['cheeseshop'].nce = nce
        sys.modules['cheeseshop.nce'] = nce
        sys.modules['cheeseshop.nce.development'] = settings
        from djangorecipe import test
        test.main('cheeseshop.nce.development',  'tilsit', 'stilton')
        self.assertEqual(execute_manager.call_args[0], (settings,))

    @mock.patch('sys.stderr.write')
    @mock.patch('sys.exit')
    def test_settings_error(self, sys_exit, stderr_write):
        # When the settings file cannot be imported the test runner
        # wil exit with a message and a specific exit code.
        from djangorecipe import test
        self.assertRaises(UnboundLocalError, test.main, 'cheeseshop.tilsit',
                          'stilton')
        self.assertEqual(stderr_write.call_args,
                         (("Error loading the settings module "
                           "'cheeseshop.tilsit': "
                           "No module named tilsit",), {}))
        self.assertEqual(sys_exit.call_args, ((1,), {}))


class TestManageScript(ScriptTestCase):

    @mock.patch('django.core.management.execute_manager')
    def test_script(self, execute_manager):
        # The manage script is a replacement for the default manage.py
        # script. It has all the same bells and whistles since all it
        # does is call the normal Django stuff.
        from djangorecipe import manage
        manage.main('cheeseshop.development')
        self.assertEqual(execute_manager.call_args,
                         ((self.settings,), {}))

    @mock.patch('sys.stderr.write')
    @mock.patch('sys.exit')
    def test_settings_error(self, sys_exit, stderr_write):
        # When the settings file cannot be imported the management
        # script it wil exit with a message and a specific exit code.
        from djangorecipe import manage
        self.assertRaises(UnboundLocalError, manage.main, 'cheeseshop.tilsit')
        self.assertEqual(stderr_write.call_args,
                         (("Error loading the settings module "
                           "'cheeseshop.tilsit': "
                           "No module named tilsit",), {}))
        self.assertEqual(sys_exit.call_args, ((1,), {}))


class TestFCGIScript(ScriptTestCase):

    @mock.patch('django.conf.settings')
    @mock.patch('django.core.management.setup_environ')
    @mock.patch('django.core.servers.fastcgi.runfastcgi')
    def test_script(self, runfastcgi, setup_environ, settings):
        # The fcgi is a warpper for the django fcgi script.
        from djangorecipe import fcgi
        settings.FCGI_OPTIONS = {}
        fcgi.main('cheeseshop.development', logfile=None)
        self.assertEqual(setup_environ.call_args,
                         ((self.settings,), {}))
        self.assertEqual(runfastcgi.call_args, {})

    @mock.patch('sys.stderr.write')
    @mock.patch('sys.exit')
    def test_settings_error(self, sys_exit, stderr_write):
        # When the settings file cannot be imported the fcgi
        # script it wil exit with a message and a specific exit code.
        from djangorecipe import fcgi
        self.assertRaises(UnboundLocalError, fcgi.main, 'cheeseshop.tilsit')
        self.assertEqual(stderr_write.call_args,
                         (("Error loading the settings module "
                           "'cheeseshop.tilsit': "
                           "No module named tilsit",), {}))
        self.assertEqual(sys_exit.call_args, ((1,), {}))


class TestWSGIScript(ScriptTestCase):

    @mock.patch('django.core.management.setup_environ')
    @mock.patch('django.core.handlers.wsgi.WSGIHandler')
    def test_script(self, WSGIHandler, setup_environ):
        # The fcgi is a warpper for the django fcgi script.
        from djangorecipe import wsgi
        wsgi.main('cheeseshop.development', logfile=None)
        self.assertEqual(WSGIHandler.call_args, {})

    @mock.patch('sys.stderr.write')
    @mock.patch('sys.exit')
    def test_settings_error(self, sys_exit, stderr_write):
        # When the settings file cannot be imported the wsgi
        # script it wil exit with a message and an specific exit code.
        from djangorecipe import wsgi
        #Catch the error that has to occur because sys.exit is patched
        #and doesn't exit automatically.
        self.assertRaises(UnboundLocalError, wsgi.main, 'cheeseshop.tilsit')
        self.assertEqual(stderr_write.call_args,
                         (("Error loading the settings module "
                           "'cheeseshop.tilsit': "
                           "No module named tilsit",), {}))
        self.assertEqual(sys_exit.call_args, ((1,), {}))


def test_suite():
    return unittest.TestSuite((
            unittest.makeSuite(TestRecipe),
            unittest.makeSuite(TestTestScript),
            unittest.makeSuite(TestManageScript),
            unittest.makeSuite(TestFCGIScript),
            unittest.makeSuite(TestWSGIScript),
            ))

if __name__ == '__main__':
        unittest.main()
