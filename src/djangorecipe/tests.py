import unittest
import tempfile
import os
import sys
import shutil

import mock
from zc.buildout import UserError
from zc.recipe.egg.egg import Scripts as ZCRecipeEggScripts

from djangorecipe.recipe import Recipe

# Add the testing dir to the Python path so we can use a fake Django
# install. This needs to be done so that we can use this as a base for
# mock's with some of the tests.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'testing'))

# Now that we have a fake Django on the path we can import the
# scripts. These are depenent on a Django install, hence the fake one.
from djangorecipe import test
from djangorecipe import manage


class TestRecipe(unittest.TestCase):

    def setUp(self):
        # Create a directory for our buildout files created by the recipe
        self.buildout_dir = tempfile.mkdtemp('djangorecipe')

        self.bin_dir = os.path.join(self.buildout_dir, 'bin')
        self.develop_eggs_dir = os.path.join(self.buildout_dir,
                                             'develop-eggs')
        self.eggs_dir = os.path.join(self.buildout_dir, 'eggs')
        self.parts_dir = os.path.join(self.buildout_dir, 'parts')

        # We need to create the bin dir since the recipe should be able to expect it exists
        os.mkdir(self.bin_dir)

        self.recipe = Recipe({'buildout': {'eggs-directory': self.eggs_dir,
                                           'develop-eggs-directory': self.develop_eggs_dir,
                                           'python': 'python-version',
                                           'bin-directory': self.bin_dir,
                                           'parts-directory': self.parts_dir,
                                           'directory': self.buildout_dir,
                                           },
                              'python-version': {'executable': sys.executable}},
                             'django',
                             {'recipe': 'djangorecipe',
                              'version': 'trunk'})

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
                Recipe({'buildout': {'eggs-directory': self.eggs_dir,
                                     'develop-eggs-directory': self.develop_eggs_dir,
                                     'python': 'python-version',
                                     'bin-directory': self.bin_dir,
                                     'parts-directory': self.parts_dir,
                                     'directory': self.buildout_dir,
                                     },
                        'python-version': {'executable': sys.executable}},
                       'django',
                       {'recipe': 'djangorecipe',
                        'version': 'trunk'}).options.copy() for i in range(2)])

    def test_svn_url(self):
        # Make sure that only a few specific type of url's are
        # considered svn url's

        # This is a plain release version so it should indicate it is
        # not a svn url
        self.failIf(self.recipe.is_svn_url('0.96.2'))
        # The next line specifies a proper link with the trunk
        self.assert_(self.recipe.is_svn_url('trunk'))
        # A url looking like trunk should also fail
        self.failIf(self.recipe.is_svn_url('trunka'))
        # A full svn url including version should work
        self.assert_(self.recipe.is_svn_url(
            'http://code.djangoproject.com/svn/django/branches/newforms-admin@7833'))
        # HTTPS should work too
        self.assert_(self.recipe.is_svn_url(
            'https://code.djangoproject.com/svn/django/branches/newforms-admin@7833'))
        # Svn+ssh should work
        self.assert_(self.recipe.is_svn_url(
            'svn+ssh://myserver/newforms-admin@7833'))
        # Svn protocol through any custom tunnel defined in ~/.subversion/config should work
        self.assert_(self.recipe.is_svn_url(
            'svn+MY_Custom-tunnel://myserver/newforms-admin@7833'))
        # Using a non existent protocol should not be a svn url?
        self.failIf(self.recipe.is_svn_url(
            'unknown://myserver/newforms-admin@7833'))

    def test_command(self):
        # The command method is a wrapper for subprocess which excutes
        # a command and return's it's status code. We will demonstrate
        # this with a simple test of running `dir`.
        self.failIf(self.recipe.command('echo'))
        # Executing a non existing command should return an error code
        self.assert_(self.recipe.command('spamspamspameggs'))

    @mock.patch('subprocess', 'Popen')
    def test_command_verbose_mode(self, popen):
        # When buildout is put into verbose mode the command methode
        # should stop capturing the ouput of it's commands.
        popen.return_value = mock.Mock()
        self.recipe.buildout['buildout']['verbosity'] = 'verbose'
        self.recipe.command('silly-command')
        self.assertEqual(
            popen.call_args,
            (('silly-command',), {'shell': True, 'stdout': None}))

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
                    [self.recipe.generate_secret() for i in xrange(10)])) > 1)

    def test_version_to_svn(self):
        # Version specification that lead to a svn repository can be
        # specified in different ways. Just specifying `trunk` should
        # be enough to get the full url to the Django trunk.
        self.assertEqual(self.recipe.version_to_svn('trunk'),
                         'http://code.djangoproject.com/svn/django/trunk/')
        # Any other specification should lead to the url it is given
        self.assertEqual(self.recipe.version_to_svn('svn://somehost/trunk'),
                         'svn://somehost/trunk')

    def test_version_to_download_suffic(self):
        # To create standard names for the download directory a method
        # is provided which converts a version to a dir suffix. A
        # simple pointer to trunk should return svn.
        self.assertEqual(self.recipe.version_to_download_suffix('trunk'),
                         'svn')
        # Any other url should return the last path component. This
        # works out nicely for branches or version pinned url's.
        self.assertEqual(self.recipe.version_to_download_suffix(
                'http://monty/branches/python'), 'python')

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
                     "djangorecipe.wsgi.main('project.development', logfile='')"
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
        self.assert_("djangorecipe.fcgi.main('project.development', logfile='')"
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

    @mock.patch('zc.buildout.easy_install', 'scripts')
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
                     
    @mock.patch('shutil', 'rmtree')
    @mock.patch('os.path', 'exists')
    @mock.patch('urllib', 'urlretrieve')
    @mock.patch('shutil', 'copytree')
    @mock.patch(ZCRecipeEggScripts, 'working_set')
    @mock.patch('zc.buildout.easy_install', 'scripts')
    @mock.patch(Recipe, 'install_release')
    @mock.patch(Recipe, 'create_manage_script')
    @mock.patch(Recipe, 'create_test_runner')
    @mock.patch('zc.recipe.egg', 'Develop')
    def test_fulfills_django_dependency(self, rmtree, path_exists, 
        urlretrieve, copytree, working_set, scripts, install_release, 
        manage, testrunner, develop):
        # Test for https://bugs.launchpad.net/djangorecipe/+bug/397864
        # djangorecipe should always fulfil the 'Django' requirement.        
        self.recipe.options['version'] = '1.0'
        path_exists.return_value = True
        working_set.return_value = (None, [])
        manage.return_value = []
        scripts.return_value = []
        testrunner.return_value = []
        develop_install = mock.Mock()
        develop.return_value = develop_install
        self.recipe.install()

        # We should see that Django was added as a develop egg.
        options = develop.call_args[0][2]
        self.assertEqual(options['location'], os.path.join(self.parts_dir, 'django'))
        
        # Check that the install() method for the develop egg was called with no args
        first_method_name, args, kwargs = develop_install.method_calls[0]
        self.assertEqual('install', first_method_name)
        self.assertEqual(0, len(args))
        self.assertEqual(0, len(kwargs))

    @mock.patch('shutil', 'rmtree')
    @mock.patch('os.path', 'exists')
    @mock.patch('urllib', 'urlretrieve')
    @mock.patch('shutil', 'copytree')
    @mock.patch(ZCRecipeEggScripts, 'working_set')
    @mock.patch('zc.buildout.easy_install', 'scripts')
    @mock.patch(Recipe, 'install_release')
    @mock.patch(Recipe, 'create_manage_script')
    @mock.patch(Recipe, 'create_test_runner')
    @mock.patch('zc.recipe.egg', 'Develop')    
    def test_extra_paths(self, rmtree, path_exists, urlretrieve,
                                   copytree, working_set, scripts,
                                   install_release, manage, testrunner,
                                   develop):
        # The recipe allows extra-paths to be specified. It uses these to
        # extend the Python path within it's generated scripts.
        self.recipe.options['version'] = '1.0'
        self.recipe.options['extra-paths'] = 'somepackage\nanotherpackage'
        path_exists.return_value = True
        working_set.return_value = (None, [])
        manage.return_value = []
        scripts.return_value = []
        testrunner.return_value = []
        develop.return_value = mock.Mock()        
        self.recipe.install()
        self.assertEqual(manage.call_args[0][0][-2:],
                         ['somepackage', 'anotherpackage'])

    @mock.patch('shutil', 'rmtree')
    @mock.patch('os.path', 'exists')
    @mock.patch('urllib', 'urlretrieve')
    @mock.patch('shutil', 'copytree')
    @mock.patch(ZCRecipeEggScripts, 'working_set')
    @mock.patch('zc.buildout.easy_install', 'scripts')
    @mock.patch(Recipe, 'install_release')
    @mock.patch(Recipe, 'create_manage_script')
    @mock.patch(Recipe, 'create_test_runner')
    @mock.patch('site', 'addsitedir')
    @mock.patch('zc.recipe.egg', 'Develop')    
    def test_pth_files(self, rmtree, path_exists, urlretrieve,
                       copytree, working_set, scripts,
                       install_release, manage, testrunner, addsitedir,
                       develop):
        # When a pth-files option is set the recipe will use that to add more
        # paths to extra-paths.
        self.recipe.options['version'] = '1.0'
        path_exists.return_value = True
        working_set.return_value = (None, [])
        scripts.return_value = []
        manage.return_value = []
        testrunner.return_value = []
        develop.return_value = mock.Mock()
        
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

    @mock.patch('urllib2', 'urlopen')
    def test_get_release(self, mock):
        # The get_release method fecthes a release tarball and
        # extracts it. We have setup a mock so that it won't actually
        # download the release. Let's call the code.
        class FakeFile(object):
            def read(self):
                return 'Django tarball'
            def close(self):
                self.closed = True

        tmp = tempfile.mkdtemp()
        filename = os.path.join(tmp, 'django-0.96.2.tar.gz')
        mock.return_value = FakeFile()
        try:
            self.assertEqual(
                self.recipe.get_release('0.96.2', tmp),
                filename)
            # It tried to download the release through our mock
            mock.assert_called_with(
                'http://www.djangoproject.com/download/0.96.2/tarball/')
            # The file should have been filled with the contents from the
            # handle it got.
            self.assertEqual(open(filename).read(), 'Django tarball')
        finally:
            shutil.rmtree(tmp)

    @mock.patch('setuptools.archive_util', 'unpack_archive')
    @mock.patch('shutil', 'move')
    @mock.patch('shutil', 'rmtree')
    @mock.patch('os', 'listdir')
    def test_install_release(self, unpack, move, rmtree, listdir):
        # To install a release the recipe uses a specific method. We
        # have have mocked all the calls which interact with the
        # filesystem.
        listdir.return_value = ('Django-0.96-2',)
        self.recipe.install_release('0.96.2', 'downloads',
                                    'downloads/django-0.96.2.tar.gz',
                                    'parts/django')
        # Let's see what the mock's have been called with
        self.assertEqual(listdir.call_args,
                         (('downloads/django-archive',), {}))
        self.assertEqual(unpack.call_args,
                         (('downloads/django-0.96.2.tar.gz',
                           'downloads/django-archive'), {}))
        self.assertEqual(move.call_args,
                         (('downloads/django-archive/Django-0.96-2',
                           'parts/django'), {}))
        self.assertEqual(rmtree.call_args,
                         (('downloads/django-archive',), {}))

    @mock.patch('shutil', 'copytree')
    @mock.patch(Recipe, 'command')
    def test_install_svn_version(self, copytree, command):
        # Installation from svn is handled by a method. We have mocked
        # the command method to avoid actual checkouts of Django.
        self.recipe.install_svn_version('trunk', 'downloads',
                                        'parts/django', False)
        # This should have tried to do a checkout of the Django trunk
        self.assertEqual(command.call_args,
                         (('svn co http://code.djangoproject.com/svn/django/trunk/ downloads/django-svn -q',), {}))
        # A copy command to the parts directory should also have been
        # issued
        self.assertEqual(copytree.call_args,
                         (('downloads/django-svn', 'parts/django'), {}))

    @mock.patch('shutil', 'copytree')
    @mock.patch('os.path', 'exists')
    @mock.patch(Recipe, 'command')
    def test_install_and_update_svn_version(self, copytree, exists, command):
        # When an checkout has been done of a svn based installation
        # is already done the recipe should just update it.
        exists.return_value = True

        self.recipe.install_svn_version('trunk', 'downloads',
                                        'parts/django', False)
        self.assertEqual(exists.call_args, (('downloads/django-svn',), {}))
        self.assertEqual(command.call_args,
                         (('svn up -q',), {'cwd': 'downloads/django-svn'}))

    @mock.patch(Recipe, 'command')
    def test_install_broken_svn(self, command):
        # When the checkout from svn fails during a svn build the
        # installation method raises an error. We will simulate this
        # failure by telling our mock what to do.
        command.return_value = 1
        # The line above should indicate a failure (non-zero exit
        # code)
        self.assertRaises(UserError, self.recipe.install_svn_version,
                          'trunk', 'downloads', 'parts/django', False)

    @mock.patch('shutil', 'copytree')
    @mock.patch(Recipe, 'command')
    def test_svn_install_from_cache(self, copytree, command):
        # If the buildout is told to install from cache it will not do
        # a checkout but instead an existing checkout
        self.recipe.buildout['buildout']['install-from-cache'] = 'true'
        # Now we can run the installation method
        self.recipe.install_svn_version('trunk', 'downloads',
                                        'parts/django', True)
        # This should not have called the recipe's command method
        self.failIf(command.called)
        # A copy from the cache to the destination should have been
        # made
        self.assertEqual(copytree.call_args,
                         (('downloads/django-svn', 'parts/django'), {}))

    @mock.patch('shutil', 'rmtree')
    @mock.patch('os.path', 'exists')
    @mock.patch('urllib', 'urlretrieve')
    @mock.patch('shutil', 'copytree')
    @mock.patch(ZCRecipeEggScripts, 'working_set')
    @mock.patch('zc.buildout.easy_install', 'scripts')
    @mock.patch(Recipe, 'install_release')
    @mock.patch(Recipe, 'command')
    def test_update_svn(self, rmtree, path_exists, urlretrieve,
                        copytree, working_set, scripts,
                        install_release, command):
        path_exists.return_value = True
        working_set.return_value = (None, [])
        # When the recipe is asked to do an update and the version is
        # a svn version it just does an update on the parts folder.
        self.recipe.update()
        self.assertEqual('svn up -q', command.call_args[0][0])
        # It changes the working directory so that the simple svn up
        # command will work.
        self.assertEqual(command.call_args[1].keys(), ['cwd'])

    @mock.patch('shutil', 'rmtree')
    @mock.patch('os.path', 'exists')
    @mock.patch('urllib', 'urlretrieve')
    @mock.patch('shutil', 'copytree')
    @mock.patch(ZCRecipeEggScripts, 'working_set')
    @mock.patch('zc.buildout.easy_install', 'scripts')
    @mock.patch(Recipe, 'install_release')
    @mock.patch('subprocess', 'call')
    def test_update_with_cache(self, rmtree, path_exists, urlretrieve,
                               copytree, working_set, scripts,
                               install_release, call_process):
        path_exists.return_value = True
        working_set.return_value = (None, [])
        # When the recipe is asked to do an update whilst in install
        # from cache mode it just ignores it
        self.recipe.install_from_cache = True
        self.recipe.update()
        self.failIf(call_process.called)

    @mock.patch('shutil', 'rmtree')
    @mock.patch('os.path', 'exists')
    @mock.patch('urllib', 'urlretrieve')
    @mock.patch('shutil', 'copytree')
    @mock.patch(ZCRecipeEggScripts, 'working_set')
    @mock.patch('zc.buildout.easy_install', 'scripts')
    @mock.patch(Recipe, 'install_release')
    @mock.patch('subprocess', 'call')
    def test_update_with_newest_false(self, rmtree, path_exists, urlretrieve,
                                      copytree, working_set, scripts,
                                      install_release, call_process):
        path_exists.return_value = True
        working_set.return_value = (None, [])
        # When the recipe is asked to do an update whilst in install
        # from cache mode it just ignores it
        self.recipe.buildout['buildout']['newest'] = 'false'
        self.recipe.update()
        self.assertFalse(call_process.called)

    @mock.patch('shutil', 'rmtree')
    @mock.patch('os.path', 'exists')
    @mock.patch('urllib', 'urlretrieve')
    @mock.patch('shutil', 'copytree')
    @mock.patch(ZCRecipeEggScripts, 'working_set')
    @mock.patch('zc.buildout.easy_install', 'scripts')
    @mock.patch(Recipe, 'install_release')
    @mock.patch('zc.recipe.egg', 'Develop')        
    def test_clear_existing_django(self, rmtree, path_exists, urlretrieve,
                                   copytree, working_set, scripts,
                                   install_release, develop):
        # When the recipe is executed and Django is already installed
        # within parts it should remove it. We will mock the exists
        # check to make it let the recipe think it has an existing
        # Django install.
        self.recipe.options['version'] = '1.0'
        path_exists.return_value = True
        working_set.return_value = (None, [])
        scripts.return_value = []
        develop.return_value = mock.Mock()
        self.recipe.install()
        # This should have called remove tree
        self.assert_(rmtree.called)
        # We will assert that the last two compontents of the path
        # passed to rmtree are the ones we wanted to delete.
        self.assertEqual(rmtree.call_args[0][0].split('/')[-2:],
                         ['parts', 'django'])

    @mock.patch('shutil', 'rmtree')
    @mock.patch('os.path', 'exists')
    @mock.patch('urllib', 'urlretrieve')
    @mock.patch('shutil', 'copytree')
    @mock.patch(ZCRecipeEggScripts, 'working_set')
    @mock.patch('zc.buildout.easy_install', 'scripts')
    @mock.patch(Recipe, 'install_release')
    @mock.patch(Recipe, 'command')
    def test_update_pinned_svn_url(self, rmtree, path_exists, urlretrieve,
                                   copytree, working_set, scripts,
                                   install_release, command):
        path_exists.return_value = True
        working_set.return_value = (None, [])
        # Make sure that updating a pinned version is updated
        # accordingly. It must not switch to updating beyond it's
        # requested revision.
        # The recipe does this by checking for an @ sign in the url /
        # version.
        self.recipe.is_svn_url = lambda version: True

        self.recipe.options['version'] = 'http://testing/trunk@2531'
        self.recipe.update()
        self.assertEqual(command.call_args[0], ('svn up -r 2531 -q',))

    @mock.patch('shutil', 'rmtree')
    @mock.patch('os.path', 'exists')
    @mock.patch('urllib', 'urlretrieve')
    @mock.patch('shutil', 'copytree')
    @mock.patch(ZCRecipeEggScripts, 'working_set')
    @mock.patch('zc.buildout.easy_install', 'scripts')
    @mock.patch(Recipe, 'install_release')
    @mock.patch(Recipe, 'command')
    def test_update_username_in_svn_url(self, rmtree, path_exists, urlretrieve,
                                        copytree, working_set, scripts,
                                        install_release, command):
        path_exists.return_value = True
        working_set.return_value = (None, [])
        # Make sure that updating a version with a username
        # in the URL works
        self.recipe.is_svn_url = lambda version: True

        # First test with both a revision and a username in the url
        self.recipe.options['version'] = 'http://user@testing/trunk@2531'
        self.recipe.update()
        self.assertEqual(command.call_args[0], ('svn up -r 2531 -q',))

        # Now test with only the username
        self.recipe.options['version'] = 'http://user@testing/trunk'
        self.recipe.update()
        self.assertEqual(command.call_args[0], ('svn up -q',))

    def test_python_option(self):
        # The python option makes it possible to specify a specific Python
        # executable which is to be used for the generated scripts.
        recipe = Recipe({'buildout': {'eggs-directory': self.eggs_dir,
                                      'develop-eggs-directory': self.develop_eggs_dir,
                                      'python': 'python-version',
                                      'bin-directory': self.bin_dir,
                                      'parts-directory': self.parts_dir,
                                      'directory': self.buildout_dir,
                                     },
                         'python-version': {'executable': '/python4k'}},
                        'django',
                        {'recipe': 'djangorecipe', 'version': 'trunk',
                         'wsgi': 'true'})
        recipe.make_scripts([], [])
        # This should have created a script in the bin dir
        wsgi_script = os.path.join(self.bin_dir, 'django.wsgi')
        self.assertEqual(open(wsgi_script).readlines()[0], '#!/python4k\n')
        # Changeing the option for only the part will change the used Python
        # version.
        recipe = Recipe({'buildout': {'eggs-directory': self.eggs_dir,
                                      'develop-eggs-directory': self.develop_eggs_dir,
                                      'python': 'python-version',
                                      'bin-directory': self.bin_dir,
                                      'parts-directory': self.parts_dir,
                                      'directory': self.buildout_dir,
                                     },
                         'python-version': {'executable': '/python4k'},
                         'py5k': {'executable': '/python5k'}},
                        'django',
                        {'recipe': 'djangorecipe', 'version': 'trunk',
                         'python': 'py5k', 'wsgi': 'true'})
        recipe.make_scripts([], [])
        self.assertEqual(open(wsgi_script).readlines()[0], '#!/python5k\n')

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

    @mock.patch('django.core.management', 'execute_manager')
    def test_script(self, execute_manager):
        # The test script should execute the standard Django test
        # command with any apps given as its arguments.
        test.main('cheeseshop.development',  'spamm', 'eggs')
        # We only care about the arguments given to execute_manager
        self.assertEqual(execute_manager.call_args[1],
                         {'argv': ['test', 'test', 'spamm', 'eggs']})

    @mock.patch('django.core.management', 'execute_manager')
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

        test.main('cheeseshop.nce.development',  'tilsit', 'stilton')
        self.assertEqual(execute_manager.call_args[0], (settings,))

    @mock.patch('sys', 'exit')
    def test_settings_error(self, sys_exit):
        # When the settings file cannot be imported the test runner
        # wil exit with a message and a specific exit code.
        test.main('cheeseshop.tilsit', 'stilton')
        self.assertEqual(sys_exit.call_args, ((1,), {}))

class TestManageScript(ScriptTestCase):

    @mock.patch('django.core.management', 'execute_manager')
    def test_script(self, execute_manager):
        # The manage script is a replacement for the default manage.py
        # script. It has all the same bells and whistles since all it
        # does is call the normal Django stuff.
        manage.main('cheeseshop.development')
        self.assertEqual(execute_manager.call_args,
                         ((self.settings,), {}))

    @mock.patch('sys', 'exit')
    def test_settings_error(self, sys_exit):
        # When the settings file cannot be imported the management
        # script it wil exit with a message and a specific exit code.
        manage.main('cheeseshop.tilsit')
        self.assertEqual(sys_exit.call_args, ((1,), {}))

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)

    # Make a semi permanent download cache to speed up the test
    tmp = tempfile.gettempdir()
    cache_dir = os.path.join(tmp, 'djangorecipe-test-cache')
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    # Create the default.cfg which sets the download cache
    home = test.globs['tmpdir']('home')
    test.globs['mkdir'](home, '.buildout')
    test.globs['write'](home, '.buildout', 'default.cfg',
    """
[buildout]
download-cache = %(cache_dir)s
    """ % dict(cache_dir=cache_dir))
    os.environ['HOME'] = home

    zc.buildout.testing.install('zc.recipe.egg', test)
    zc.buildout.testing.install_develop('djangorecipe', test)


def test_suite():
    return unittest.TestSuite((
            unittest.makeSuite(TestRecipe),
            unittest.makeSuite(TestTestScript),
            unittest.makeSuite(TestManageScript),
            ))
