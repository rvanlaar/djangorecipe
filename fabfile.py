import os
import re

from fabric.api import env, local

version_re = re.compile(r'''version\s*=\s*['"](?P<version>[\d\.]+)['"]''')


def get_version():
    """Extract the current version from the setup.py file."""
    setup = open('setup.py').read()
    return version_re.search(setup).group('version')

env.version = get_version()


def release_djangorecipe():
    """Release Djangorecipe to PyPi."""
    version = get_version()
    test()
    local('python setup.py sdist')
    # Make sure we have a proper release that could be installed.
    local('tar xfz %s/dist/djangorecipe-%s.tar.gz -C /tmp' % (
            os.path.abspath('.'), version))
    local('cd /tmp/djangorecipe-$(version); python setup.py egg_info')
    # Release the code.
    local('python setup.py sdist register upload')


def release():
    """Release everything related to the project."""
    release_djangorecipe()
    local('bzr tag release-%(version)s' % env)


def test():
    """Create an in-place installation and run the tests."""
    local('python bootstrap.py')
    local('./bin/buildout -v')
    local('./bin/test')
