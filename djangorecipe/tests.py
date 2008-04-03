import unittest
import tempfile
import os

import zc.buildout.testing
from zope.testing import doctest, renormalizing


def djang_test_command(test):
    '''
    Make sure the test command works.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... eggs-directory = /home/jvloothuis/Projects/eggs
    ... parts = django
    ... 
    ... [django]
    ... recipe = djangorecipe
    ... version = 0.96.1
    ... settings = development
    ... project = dummyshop
    ... """)

    >>> print system(buildout),
    Upgraded:
      zc.buildout version 1.0.0,
      setuptools version ...;
    restarting.
    Generated script '/sample-buildout/bin/buildout'.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Installing django.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Generated script '/sample-buildout/bin/django'.

    Run the test command.

    >>> print system('bin/django test'),
    Creating test database...
    ...
    ----------------------------------------------------------------------
    Ran ... tests in ...
    <BLANKLINE>
    OK
    '''

def download_release(test):
    '''
    Downloading releases should work.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... eggs-directory = /home/jvloothuis/Projects/eggs
    ... parts = django
    ... 
    ... [django]
    ... recipe = djangorecipe
    ... version = trunk
    ... settings = development
    ... project = dummyshop
    ... """)

    >>> print system(buildout),
    Upgraded:
      zc.buildout version 1.0.0,
      setuptools version ...;
    restarting.
    Generated script '/sample-buildout/bin/buildout'.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Installing django.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Generated script '/sample-buildout/bin/django'.

    Make sure the version number matches the requested version.

    >>> system('bin/django --version')
    '...-pre-SVN-...'

    '''

def use_trunk(test):
    '''
    Downloading releases should work.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... eggs-directory = /home/jvloothuis/Projects/eggs
    ... parts = django
    ... 
    ... [django]
    ... recipe = djangorecipe
    ... version = 0.96.1
    ... settings = development
    ... project = dummyshop
    ... """)

    >>> print system(buildout),
    Upgraded:
      zc.buildout version 1.0.0,
      setuptools version ...;
    restarting.
    Generated script '/sample-buildout/bin/buildout'.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Installing django.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Generated script '/sample-buildout/bin/django'.

    Make sure the version number matches the requested version.

    >>> print system('bin/django --version'),
    0.96.1
    '''

def test_runner(test):
    ''' 
    The test options can be used to specify a number of apps to test.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... eggs-directory = /home/jvloothuis/Projects/eggs
    ... parts = django
    ... 
    ... [django]
    ... recipe = djangorecipe
    ... version = trunk
    ... settings = development
    ... test = someapp
    ... project = dummy
    ... """)

    >>> print system(buildout),
    Upgraded:
      zc.buildout version 1.0.0,
      setuptools version ...;
    restarting.
    Generated script '/sample-buildout/bin/buildout'.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Installing django.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Generated script '/sample-buildout/bin/django'.
    Generated script '/sample-buildout/bin/test'.

    The apps are not installed so running the tests will break it.

    >>> print system('bin/test'),
    Traceback (most recent call last):
    ...
    django.core.exceptions.ImproperlyConfigured: App with label someapp could not be found


    Now we will create an app so that the test will run.

    >>> mkdir('dummy/someapp')
    >>> write('dummy/someapp/__init__.py', '')
    >>> write('dummy/someapp/urls.py', '')
    >>> write('dummy/someapp/views.py', '')
    >>> write('dummy/someapp/models.py', '')
    >>> write('dummy/someapp/tests.py',
    ... """
    ... import doctest
    ...
    ... def simple_test(test):
    ...     \'\'\'
    ...     >>> 1 == 2
    ...     False
    ...     \'\'\'
    ...
    ... def suite():
    ...     return doctest.DocTestSuite()
    ... """)

    We need to add the app to the installed apps.

    >>> write('dummy/development.py',
    ... """
    ... from dummy.settings import *
    ... INSTALLED_APPS = (
    ...     'django.contrib.auth',
    ...     'django.contrib.contenttypes',
    ...     'django.contrib.sessions',
    ...     'django.contrib.admin',
    ...     'dummy.someapp',
    ... )
    ... """)

    >>> print system('bin/test'),
    Creating test database...
    ...
    Destroying test database...
    .
    ----------------------------------------------------------------------
    Ran 1 test in ...
    <BLANKLINE>
    OK

    '''

def test_existing_project(test):
    ''' 
    An existing project should not be overwritten when doing a new
    buildout.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... eggs-directory = /home/jvloothuis/Projects/eggs
    ... parts = django
    ... 
    ... [django]
    ... recipe = djangorecipe
    ... version = 0.96.1
    ... settings = development
    ... test = someapp
    ... project = dummy
    ... """)

    >>> mkdir('dummy')
    >>> mkdir('dummy/media')
    >>> mkdir('dummy/templates')
    >>> write('dummy/settings.py', 'TESTING')

    >>> print system(buildout),
    Upgraded:
      zc.buildout version 1.0.0,
      setuptools version ...;
    restarting.
    Generated script '/sample-buildout/bin/buildout'.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Installing django.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Generated script '/sample-buildout/bin/django'.
    Generated script '/sample-buildout/bin/test'.
    Skipping creating of project: dummy since it exists

    The settings should still be filled with our test content.

    >>> cat('dummy/settings.py')
    TESTING
    '''

def test_existing_django_dir(test):
    '''
    If there is an existing Django installation (from a previous
    buildout) in the way the recipe should just remove it.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... eggs-directory = /home/jvloothuis/Projects/eggs
    ... parts = django
    ... 
    ... [django]
    ... recipe = djangorecipe
    ... version = 0.96.1
    ... settings = development
    ... project = dummy
    ... """)

    >>> mkdir('parts/django')

    >>> print system(buildout),
    Upgraded:
      zc.buildout version 1.0.0,
      setuptools version ...;
    restarting.
    Generated script '/sample-buildout/bin/buildout'.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Installing django.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Generated script '/sample-buildout/bin/django'.

    '''

def test_wsgi(test):
    '''
    The recipe has an option to generate a WSGI script which can be
    used with mod_wsgi.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... eggs-directory = /home/jvloothuis/Projects/eggs
    ... parts = django
    ... 
    ... [django]
    ... recipe = djangorecipe
    ... version = 0.96.1
    ... settings = development
    ... project = dummy
    ... wsgi = true
    ... """)

    >>> print system(buildout),
    Upgraded:
      zc.buildout version 1.0.0,
      setuptools version ...;
    restarting.
    Generated script '/sample-buildout/bin/buildout'.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Installing django.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Generated script '/sample-buildout/bin/django'.

    >>> cat('bin/django.wsgi')
    <BLANKLINE>
    ...
    application = django.core.handlers.wsgi.WSGIHandler()

    '''

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
download-directory = %(cache_dir)s
    """ % dict(cache_dir=cache_dir))
    os.environ['HOME'] = home

    zc.buildout.testing.install('zc.recipe.egg', test)
    zc.buildout.testing.install_develop('djangorecipe', test)


def test_suite():
    return unittest.TestSuite((
            doctest.DocTestSuite(
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=doctest.ELLIPSIS,
                checker=renormalizing.RENormalizing([
                        zc.buildout.testing.normalize_path,
                        zc.buildout.testing.normalize_script,
                        zc.buildout.testing.normalize_egg_py]))))

