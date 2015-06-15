import os
import shutil
import sys
import tempfile
import unittest

import mock
from zc.buildout import UserError

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
                'bin-directory': self.bin_dir,
                'parts-directory': self.parts_dir,
                'directory': self.buildout_dir,
                'python': 'buildout',
                'executable': sys.executable,
                'find-links': '',
                'allow-hosts': ''},
             },
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

    @mock.patch('zc.recipe.egg.egg.Scripts.working_set',
                return_value=(None, []))
    def test_update_smoketest(self, working_set):
        working_set  # noqa
        self.recipe.install()
        self.recipe.update()

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

    def test_version_option_deprecation1(self):
        options = {'recipe': 'djangorecipe',
                   'version': 'trunk',
                   'wsgi': 'true'}
        self.assertRaises(UserError, Recipe, *('buildout', 'test', options))

    def test_version_option_deprecation2(self):
        options = {'recipe': 'djangorecipe',
                   'wsgilog': 'something'}
        self.assertRaises(UserError, Recipe, *('buildout', 'test', options))

    def test_version_option_deprecation3(self):
        options = {'recipe': 'djangorecipe',
                   'projectegg': 'something'}
        self.assertRaises(UserError, Recipe, *('buildout', 'test', options))

    def test_version_option_deprecation4(self):
        options = {'recipe': 'djangorecipe',
                   'deploy_script_extra': 'something'}
        self.assertRaises(UserError, Recipe, *('buildout', 'test', options))

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

    def test_settings_option(self):
        # The settings option can be used to specify the settings file
        # for Django to use. By default it uses `development`.
        self.assertEqual(self.recipe.options['settings'], 'development')
        # When we change it an generate a manage script it will use
        # this var.
        self.recipe.options['settings'] = 'spameggs'
        self.recipe.create_manage_script([], [])
        manage = os.path.join(self.bin_dir, 'django')
        self.assertTrue("djangorecipe.binscripts.manage('project.spameggs')"
                        in open(manage).read())

    def test_dotted_settings_path_option(self):
        self.assertEqual(self.recipe.options['settings'], 'development')
        self.recipe.options['dotted-settings-path'] = 'myproj.conf.production'
        self.recipe.create_manage_script([], [])
        manage = os.path.join(self.bin_dir, 'django')
        self.assertTrue("djangorecipe.binscripts.manage('myproj.conf.production')"
                        in open(manage).read())


class TestRecipeScripts(BaseTestRecipe):

    def test_make_protocol_script_wsgi(self):
        # To ease deployment a WSGI script can be generated. The
        # script adds any paths from the `extra_paths` option to the
        # Python path.
        self.recipe.options['wsgi'] = 'true'
        self.recipe.make_wsgi_script([], [])
        # This should have created a script in the bin dir

        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        self.assertTrue(os.path.exists(wsgi_script))

    def test_contents_protocol_script_wsgi(self):
        self.recipe.options['wsgi'] = 'true'
        self.recipe.make_wsgi_script([], [])
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')

        # The contents should list our paths
        contents = open(wsgi_script).read()
        # It should also have a reference to our settings module
        self.assertTrue('project.development' in contents)
        # and a line which set's up the WSGI app
        self.assertTrue("application = "
                        "djangorecipe.binscripts.wsgi('project.development', "
                        "logfile='')"
                        in contents)
        self.assertTrue("class logger(object)" not in contents)

    def test_contents_protocol_script_wsgi_with_initialization(self):
        self.recipe.options['wsgi'] = 'true'
        self.recipe.options['initialization'] = 'import os\nassert True'
        self.recipe.make_wsgi_script([], [])
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        self.assertTrue('import os\nassert True\n\nimport djangorecipe'
                        in open(wsgi_script).read())

    def test_contents_log_protocol_script_wsgi(self):
        self.recipe.options['wsgi'] = 'true'
        self.recipe.options['logfile'] = '/foo'
        self.recipe.make_wsgi_script([], [])

        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        contents = open(wsgi_script).read()

        self.assertTrue("logfile='/foo'" in contents)

    def test_make_protocol_named_script_wsgi(self):
        # A wsgi-script name option is specified
        self.recipe.options['wsgi'] = 'true'
        self.recipe.options['wsgi-script'] = 'foo-wsgi.py'
        self.recipe.make_wsgi_script([], [])
        wsgi_script = os.path.join(self.bin_dir, 'foo-wsgi.py')
        self.assertTrue(os.path.exists(wsgi_script))

    def test_deploy_script_extra(self):
        extra_val = '#--deploy-script-extra--'
        self.recipe.options['wsgi'] = 'true'
        self.recipe.options['deploy-script-extra'] = extra_val
        self.recipe.make_wsgi_script([], [])
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        contents = open(wsgi_script).read()
        self.assertTrue(extra_val in contents)

    @mock.patch('zc.buildout.easy_install.scripts',
                return_value=['some-path'])
    def test_make_protocol_scripts_return_value(self, scripts):
        # The return value of make scripts lists the generated scripts.
        self.recipe.options['wsgi'] = 'true'
        self.assertEqual(self.recipe.make_wsgi_script([], []),
                         ['some-path'])

    def test_create_manage_script(self):
        # This buildout recipe creates a alternative for the standard
        # manage.py script. It has all the same functionality as the
        # original one but it sits in the bin dir instead of within
        # the project.
        manage = os.path.join(self.bin_dir, 'django')
        self.recipe.create_manage_script([], [])
        self.assertTrue(os.path.exists(manage))

    def test_create_manage_script_with_initialization(self):
        manage = os.path.join(self.bin_dir, 'django')
        self.recipe.options['initialization'] = 'import os\nassert True'
        self.recipe.create_manage_script([], [])
        self.assertTrue('import os\nassert True\n\nimport djangorecipe'
                        in open(manage).read())

    def test_dotted_settings_path_option(self):
        self.assertEqual(self.recipe.options['settings'], 'development')
        self.recipe.options['wsgi'] = 'true'
        self.recipe.options['dotted-settings-path'] = 'myproj.conf.production'
        self.recipe.make_wsgi_script([], [])
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        self.assertTrue("application = "
                        "djangorecipe.binscripts.wsgi('myproj.conf.production', "
                        "logfile='')"
                        in open(wsgi_script).read())

    def test_create_scripts_with_settings(self):
        # easy_install is available. It isn't useful, but it is a good
        # example.
        self.recipe.options['scripts-with-settings'] = 'easy_install'
        created = os.path.join(self.bin_dir, 'easy_install-with-settings')
        self.recipe.create_scripts_with_settings([], [])
        self.assertTrue(os.path.exists(created))

    def test_create_scripts_with_settings2(self):
        # easy_install is available. It isn't useful, but it is a good
        # example.
        self.recipe.options['scripts-with-settings'] = 'easy_install'
        created = os.path.join(self.bin_dir, 'easy_install-with-settings')
        self.recipe.create_scripts_with_settings([], [])
        self.assertTrue(
            "os.environ['DJANGO_SETTINGS_MODULE'] = 'project.development"
            in open(created, 'r').read())

    def test_create_scripts_with_settings3(self):
        self.recipe.options['scripts-with-settings'] = 'unavailable'
        self.assertRaises(
            UserError,  # "Script name not found"
            self.recipe.create_scripts_with_settings,
            *([], []))

    def test_create_scripts_with_settings4(self):
        # By default, nothing is generated.
        result = self.recipe.create_scripts_with_settings([], [])
        self.assertEquals([], result)


class TestTesTRunner(BaseTestRecipe):

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
        self.assertFalse(os.path.exists(testrunner))

    def test_create_test_runner_with_initialization(self):
        recipe_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))
        testrunner = os.path.join(self.bin_dir, 'test')

        # When we specify an app to test it should create the the
        # testrunner
        self.recipe.options['test'] = 'knight'
        self.recipe.options['initialization'] = 'import os\nassert True'
        self.recipe.create_test_runner([recipe_dir], [])
        self.assertTrue('import os\nassert True\n\nimport djangorecipe'
                        in open(testrunner).read())

    def test_relative_paths_default(self):
        self.recipe.options['wsgi'] = 'true'

        self.recipe.make_wsgi_script([], [])
        self.recipe.create_manage_script([], [])

        manage = os.path.join(self.bin_dir, 'django')
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')

        expected = 'base = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))'
        self.assertFalse(expected in open(manage).read())
        self.assertFalse(expected in open(wsgi_script).read())

    def test_relative_paths_true(self):
        recipe = Recipe(
            {'buildout': {
                'eggs-directory': self.eggs_dir,
                'develop-eggs-directory': self.develop_eggs_dir,
                'python': 'python-version',
                'bin-directory': self.bin_dir,
                'parts-directory': self.parts_dir,
                'directory': self.buildout_dir,
                'find-links': '',
                'allow-hosts': '',
                'develop': '.',
                'relative-paths': 'true'},
             'python-version': {'executable': sys.executable}
         },
            'django',
            {'recipe': 'djangorecipe',
             'wsgi': 'true'})
        recipe.make_wsgi_script([], [])
        recipe.create_manage_script([], [])

        manage = os.path.join(self.bin_dir, 'django')
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')

        expected = 'base = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))'
        self.assertTrue(expected in open(manage).read())
        self.assertTrue(expected in open(wsgi_script).read())
