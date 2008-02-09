import unittest
import tempfile
import os

import zc.buildout.testing
from zope.testing import doctest, renormalizing


def test_command(test):
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
      setuptools version 0.6c7;
    restarting.
    Generated script '/sample-buildout/bin/buildout'.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Installing django.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Generated script '/sample-buildout/bin/django'.

    Run the test command.

    >>> print system('bin/django test'), # doctest: +ELLIPSIS
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
      setuptools version 0.6c7;
    restarting.
    Generated script '/sample-buildout/bin/buildout'.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Installing django.
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Couldn't find index page for 'zc.recipe.egg' (maybe misspelled?)
    Generated script '/sample-buildout/bin/django'.

    Make sure the version number matches the requested version.

    >>> system('bin/django --version') # doctest: +ELLIPSIS
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
      setuptools version 0.6c7;
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
                checker=renormalizing.RENormalizing([
                        zc.buildout.testing.normalize_path,
                        zc.buildout.testing.normalize_script,
                        zc.buildout.testing.normalize_egg_py]))))

