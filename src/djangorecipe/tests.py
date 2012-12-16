import copy
import os
import shutil
import sys
import tempfile
import unittest

import mock

from djangorecipe.recipe import Recipe


class BaseTestRecipe(unittest.TestCase):

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

        self.recipe_initialisation = [
            {'buildout': {
                'eggs-directory': self.eggs_dir,
                'develop-eggs-directory': self.develop_eggs_dir,
                'python': 'python-version',
                'bin-directory': self.bin_dir,
                'parts-directory': self.parts_dir,
                'directory': self.buildout_dir,
                'find-links': '',
                'allow-hosts': ''},
             'python-version': {'executable': sys.executable}},
            'django',
            {'recipe': 'djangorecipe'}]

        self.recipe = Recipe(*self.recipe_initialisation)

    def tearDown(self):
        # Remove our test dir
        shutil.rmtree(self.buildout_dir)


class TestRecipe(BaseTestRecipe):

    def test_consistent_options(self):
        # Buildout is pretty clever in detecting changing options. If
        # the recipe modifies it's options during initialisation it
        # will store this to determine wheter it needs to update or do
        # a uninstall & install. We need to make sure that we normally
        # do not trigger this. That means running the recipe with the
        # same options should give us the same results.
        self.assertEqual(Recipe(*self.recipe_initialisation).options,
                         Recipe(*self.recipe_initialisation).options)

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
        self.assertEqual(
            10, len(set(self.recipe.generate_secret() for i in range(10))))

    def test_make_protocol_script_wsgi(self):
        # To ease deployment a WSGI script can be generated. The
        # script adds any paths from the `extra_paths` option to the
        # Python path.
        self.recipe.options['wsgi'] = 'true'
        self.recipe.make_scripts([], [])
        # This should have created a script in the bin dir

        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        self.assertTrue(os.path.exists(wsgi_script))

    def test_contents_protocol_script_wsgi(self):
        self.recipe.options['wsgi'] = 'true'
        self.recipe.make_scripts([], [])
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')

        # The contents should list our paths
        contents = open(wsgi_script).read()
         # It should also have a reference to our settings module
        self.assertTrue('project.development' in contents)
         # and a line which set's up the WSGI app
        self.assertTrue("application = "
                        "djangorecipe.wsgi.main('project.development', "
                        "logfile='')"
                        in contents)
        self.assertTrue("class logger(object)" not in contents)

    def test_make_protocol_script_fcgi(self):
        self.recipe.options['fcgi'] = 'true'
        self.recipe.make_scripts([], [])

        fcgi_script = os.path.join(self.bin_dir, 'django.fcgi')
        self.assertTrue(os.path.exists(fcgi_script))

        contents = open(fcgi_script).read()
         # It should also have a reference to our settings module
        self.assertTrue('project.development' in contents)
         # and a line which set's up the FCGI app
        self.assertTrue("djangorecipe.fcgi.main('project.development', "
                        "logfile='')"
                        in contents)
        self.assertTrue("class logger(object)" not in contents)

    def test_contents_log_protocol_script_wsgi(self):
        self.recipe.options['wsgi'] = 'true'
        self.recipe.options['logfile'] = '/foo'
        self.recipe.make_scripts([], [])

        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        contents = open(wsgi_script).read()

        self.assertTrue("logfile='/foo'" in contents)

    def test_contents_log_protocol_script_fcgi(self):
        self.recipe.options['fcgi'] = 'true'
        self.recipe.options['logfile'] = '/foo'
        self.recipe.make_scripts([], [])

        fcgi_script = os.path.join(self.bin_dir, 'django.fcgi')
        contents = open(fcgi_script).read()

        self.assertTrue("logfile='/foo'" in contents)

    @mock.patch('zc.buildout.easy_install.scripts',
                return_value=['some-path'])
    def test_make_protocol_scripts_return_value(self, scripts):
        # The return value of make scripts lists the generated scripts.
        self.recipe.options['wsgi'] = 'true'
        self.recipe.options['fcgi'] = 'true'
        self.assertEqual(self.recipe.make_scripts([], []),
                         ['some-path', 'some-path'])

    def test_create_test_runner(self):
        # An executable script can be generated which will make it
        # possible to execute the Django test runner. This options
        # only works if we specify one or apps to test.
        testrunner = os.path.join(self.bin_dir, 'test')

        # This first argument sets extra_paths, we will use this to
        # make sure the script can find this recipe
        recipe_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))

        # When we specify an app to test it should create the the
        # testrunner
        self.recipe.options['test'] = 'knight'
        self.recipe.create_test_runner([recipe_dir], [])
        self.assertTrue(os.path.exists(testrunner))

    def test_not_create_test_runner(self):
        recipe_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))
        self.recipe.create_test_runner([recipe_dir], [])

        testrunner = os.path.join(self.bin_dir, 'test')

        # Show it does not create a test runner by default
        self.failIf(os.path.exists(testrunner))

    def test_create_manage_script(self):
        # This buildout recipe creates a alternative for the standard
        # manage.py script. It has all the same functionality as the
        # original one but it sits in the bin dir instead of within
        # the project.
        manage = os.path.join(self.bin_dir, 'django')
        self.recipe.create_manage_script([], [])
        self.assertTrue(os.path.exists(manage))

    def test_create_manage_script_projectegg(self):
        # When a projectegg is specified, then the egg specified
        # should get used as the project file.
        manage = os.path.join(self.bin_dir, 'django')
        self.recipe.options['projectegg'] = 'spameggs'
        self.recipe.create_manage_script([], [])
        self.assert_(os.path.exists(manage))
        # Check that we have 'spameggs' as the project
        self.assertTrue("djangorecipe.manage.main('spameggs.development')"
                        in open(manage).read())

    @mock.patch('zc.recipe.egg.egg.Scripts.working_set',
                return_value=(None, []))
    @mock.patch('djangorecipe.recipe.Recipe.create_manage_script')
    def test_extra_paths(self, manage, working_set):

        # The recipe allows extra-paths to be specified. It uses these to
        # extend the Python path within it's generated scripts.
        self.recipe.options['version'] = '1.0'
        self.recipe.options['extra-paths'] = 'somepackage\nanotherpackage'

        self.recipe.install()
        self.assertEqual(manage.call_args[0][0][-2:],
                         ['somepackage', 'anotherpackage'])

    @mock.patch('zc.recipe.egg.egg.Scripts.working_set',
                return_value=(None, []))
    @mock.patch('site.addsitedir', return_value=['extra', 'dirs'])
    def test_pth_files(self, addsitedir, working_set):

        # When a pth-files option is set the recipe will use that to add more
        # paths to extra-paths.
        self.recipe.options['version'] = '1.0'

        # The mock values needed to demonstrate the pth-files option.
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

        self.assertTrue(os.path.exists(wsgi))
        # Check that we have 'spameggs' as the project
        self.assertTrue('spameggs.development' in open(wsgi).read())

    def test_settings_option(self):
        # The settings option can be used to specify the settings file
        # for Django to use. By default it uses `development`.
        self.assertEqual(self.recipe.options['settings'], 'development')
        # When we change it an generate a manage script it will use
        # this var.
        self.recipe.options['settings'] = 'spameggs'
        self.recipe.create_manage_script([], [])
        manage = os.path.join(self.bin_dir, 'django')
        self.assertTrue("djangorecipe.manage.main('project.spameggs')"
                        in open(manage).read())

    def test_python_option(self):
        # The python option makes it possible to specify a specific Python
        # executable which is to be used for the generated scripts.
        recipe_args = copy.deepcopy(self.recipe_initialisation)
        recipe_args[0]['python-version']['executable'] = '/python4k'
        recipe_args[2]['wsgi'] = 'true'
        recipe = Recipe(*recipe_args)
        recipe.make_scripts([], [])
        # This should have created a script in the bin dir
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        self.assertEqual(open(wsgi_script).readlines()[0], '#!/python4k\n')
        # Changing the option for only the part will change the used Python
        # version.
        recipe_args[0]['py5k'] = {'executable': '/python5k'}
        recipe_args[2]['python'] = 'py5k'
        recipe = Recipe(*recipe_args)
        recipe.make_scripts([], [])
        self.assertEqual(open(wsgi_script).readlines()[0], '#!/python5k\n')

    def test_create_project(self):
        # If a project does not exist already the recipe will create
        # one.
        project_dir = os.path.join(self.buildout_dir, 'project')
        self.recipe.create_project(project_dir)

        # This should have create a project directory
        self.assertTrue(os.path.exists(project_dir))
        # With this directory we should have a list of files.
        for f in ('settings.py', 'development.py', 'production.py',
                  '__init__.py', 'urls.py', 'media', 'templates'):
            self.assertTrue(
                os.path.exists(os.path.join(project_dir, f)))

    def test_versions_deprecation(self):
        from zc.buildout import UserError
        options = {'recipe': 'djangorecipe',
                   'version': 'trunk',
                   'python': 'py5k', 'wsgi': 'true'}
        self.assertRaises(UserError, Recipe, *('buildout', 'test', options))


class TestBoilerplate(BaseTestRecipe):

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

        recipe_args = copy.deepcopy(self.recipe_initialisation)

        recipe_args[0]['versions'] = {'django': '1.2.5'}
        recipe = Recipe(*recipe_args)

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

    @mock.patch('sys.stderr')
    @mock.patch('sys.exit')
    def test_settings_error(self, sys_exit, stderr):
        # When the settings file cannot be imported the test runner
        # wil exit with a message and a specific exit code.
        from djangorecipe import test
        self.assertRaises(UnboundLocalError, test.main, 'cheeseshop.tilsit',
                          'stilton')
        self.assertEqual(stderr.write.call_args,
                         (("Error loading the settings module "
                           "'cheeseshop.tilsit': "
                           "No module named tilsit",), {}))
        self.assertEqual(sys_exit.call_args, ((1,), {}))


class TestManageScript(ScriptTestCase):

    @mock.patch('django.core.management.execute_manager')
    def test_script_pre_14(self, execute_manager):
        # The manage script is a replacement for the default manage.py
        # script. It has all the same bells and whistles since all it
        # does is call the normal Django stuff.
        from djangorecipe import manage
        manage.main_pre_14('cheeseshop.development')
        self.assertEqual(execute_manager.call_args,
                         ((self.settings,), {}))

    @mock.patch('django.core.management.execute_from_command_line')
    @mock.patch('os.environ.setdefault')
    def test_script_14(self, mock_setdefault, mock_execute):
        # The manage script is a replacement for the default manage.py
        # script. It has all the same bells and whistles since all it
        # does is call the normal Django stuff.
        from djangorecipe import manage
        manage.main_14('cheeseshop.development')
        self.assertEqual(mock_execute.call_args,
                         ((sys.argv,), {}))
        self.assertEqual(
            mock_setdefault.call_args,
            (('DJANGO_SETTINGS_MODULE', 'cheeseshop.development'), {}))

    @mock.patch('djangorecipe.manage.main_pre_14')
    @mock.patch('djangorecipe.manage.main_14')
    @mock.patch('django.VERSION', new=(1, 3, 0))
    def test_django_pre_13_selection(self, mock_14, mock_pre_14):
        from djangorecipe import manage
        manage.main('cheeseshop.development')
        self.assertTrue(mock_pre_14.called)
        self.assertFalse(mock_14.called)

    @mock.patch('djangorecipe.manage.main_pre_14')
    @mock.patch('djangorecipe.manage.main_14')
    @mock.patch('django.VERSION', new=(1, 4, 0))
    def test_django_pre_14_selection(self, mock_14, mock_pre_14):
        from djangorecipe import manage
        manage.main('cheeseshop.development')
        self.assertTrue(mock_14.called)
        self.assertFalse(mock_pre_14.called)

    @mock.patch('sys.stderr')
    @mock.patch('sys.exit')
    def test_settings_error_pre_14(self, sys_exit, stderr):
        # When the settings file cannot be imported the management
        # script it wil exit with a message and a specific exit code.
        # (Not on django 1.4, btw).
        from djangorecipe import manage
        self.assertRaises(UnboundLocalError,
                          manage.main_pre_14,
                          'cheeseshop.tilsit')
        self.assertEqual(stderr.write.call_args,
                         (("Error loading the settings module "
                           "'cheeseshop.tilsit': "
                           "No module named tilsit",), {}))
        self.assertEqual(sys_exit.call_args, ((1,), {}))


class TestFCGIScript(ScriptTestCase):

    @mock.patch('django.conf.settings')
    @mock.patch('django.core.management.setup_environ')
    @mock.patch('django.core.servers.fastcgi.runfastcgi')
    def test_script(self, runfastcgi, setup_environ, settings):
        # The fcgi is a wrapper for the django fcgi script.
        from djangorecipe import fcgi
        settings.FCGI_OPTIONS = {}
        fcgi.main('cheeseshop.development', logfile=None)
        self.assertEqual(setup_environ.call_args,
                         ((self.settings,), {}))
        self.assertEqual(runfastcgi.call_args, {})

    @mock.patch('sys.stderr')
    @mock.patch('sys.exit')
    def test_settings_error(self, sys_exit, stderr):
        # When the settings file cannot be imported the fcgi
        # script it wil exit with a message and a specific exit code.
        from djangorecipe import fcgi
        self.assertRaises(UnboundLocalError, fcgi.main, 'cheeseshop.tilsit')
        self.assertEqual(stderr.write.call_args,
                         (("Error loading the settings module "
                           "'cheeseshop.tilsit': "
                           "No module named tilsit",), {}))
        self.assertEqual(sys_exit.call_args, ((1,), {}))


class TestWSGIScript(ScriptTestCase):

    @mock.patch('django.core.management.setup_environ')
    @mock.patch('django.core.handlers.wsgi.WSGIHandler')
    def test_script(self, WSGIHandler, setup_environ):
        # The wsgi is a wrapper for the django wsgi script.
        from djangorecipe import wsgi
        wsgi.main('cheeseshop.development', logfile=None)
        self.assertEqual(WSGIHandler.call_args, {})

    @mock.patch('sys.stderr')
    @mock.patch('sys.exit')
    def test_settings_error(self, sys_exit, stderr):
        # When the settings file cannot be imported the wsgi
        # script it wil exit with a message and an specific exit code.
        from djangorecipe import wsgi
        #Catch the error that has to occur because sys.exit is patched
        #and doesn't exit automatically.
        self.assertRaises(UnboundLocalError, wsgi.main, 'cheeseshop.tilsit')
        self.assertEqual(stderr.write.call_args,
                         (("Error loading the settings module "
                           "'cheeseshop.tilsit': "
                           "No module named tilsit",), {}))
        self.assertEqual(sys_exit.call_args, ((1,), {}))
