from fabric.api import local

def build():
    """Create an in-place installation and run the tests."""

    local('python bootstrap.py')
    local('./bin/buildout -v')
    local('./bin/test')
