Description
===========

This buildout recipe can be used to create a setup for Django. It will
automatically download Django and install it in the buildout's
sandbox.

You can see an example of how to use the recipe below::

  [buildout]
  parts = satchmo django
  eggs =
    ipython
  versions = versions

  [versions]
  django = 1.2.5


  [satchmo]
  recipe = gocept.download
  url = http://www.satchmoproject.com/snapshots/satchmo-0.6.tar.gz
  md5sum = 659a4845c1c731be5cfe29bfcc5d14b1

  [django]
  recipe = djangorecipe
  settings = development
  eggs = ${buildout:eggs}
  extra-paths =
    ${satchmo:location}
  project = dummyshop


Supported options
=================

The recipe supports the following options.

project
  This option sets the name for your project. The recipe will create a
  basic structure if the project is not already there.

projectegg
  Use this instead of the project option when you want to use an egg
  as the project. This disables the generation of the project
  structure.

python
  This option can be used to specify a specific Python version which can be a
  different version from the one used to run the buildout.

settings
  You can set the name of the settings file which is to be used with
  this option. This is useful if you want to have a different
  production setup from your development setup. It defaults to
  `development`.

extra-paths
  All paths specified here will be used to extend the default Python
  path for the `bin/*` scripts.

pth-files
  Adds paths found from a site `.pth` file to the extra-paths.
  Useful for things like Pinax which maintains its own external_libs dir.

control-script
  The name of the script created in the bin folder. This script is the
  equivalent of the `manage.py` Django normally creates. By default it
  uses the name of the section (the part between the `[ ]`).

wsgi
  An extra script is generated in the bin folder when this is set to
  `true`. This can be used with mod_wsgi to deploy the project. The
  name of the script is `control-script.wsgi`.

wsgilog
  In case the WSGI server you're using does not allow printing to stdout,
  you can set this variable to a filesystem path - all stdout/stderr data
  is redirected to the log instead of printed

fcgi
  Like `wsgi` this creates an extra script within the bin folder. This
  script can be used with an FCGI deployment.

test
  If you want a script in the bin folder to run all the tests for a
  specific set of apps this is the option you would use. Set this to
  the list of app labels which you want to be tested.

testrunner
  This is the name of the testrunner which will be created. It
  defaults to `test`.

All following options only have effect when the project specified by
the project option has not been created already.

urlconf
  You can set this to a specific url conf. It will use project.urls by
  default.

secret
  The secret to use for the `settings.py`, it generates a random
  string by default.


FCGI specific settings
======================

Options for FCGI can be set within a settings file (`settings.py`). The options
is `FCGI_OPTIONS`. It should be set to a dictionary. The part below is an
example::

  FCGI_OPTIONS = {
      'method': 'threaded',
  }


Another example
===============

The next example shows you how to use some more of the options::

  [buildout]
  parts = django extras
  eggs =
    hashlib

  [extras]
  recipe = iw.recipe.subversion
  urls =
    http://django-command-extensions.googlecode.com/svn/trunk/ django-command-extensions
    http://django-mptt.googlecode.com/svn/trunk/ django-mptt

  [django]
  recipe = djangorecipe
  settings = development
  project = exampleproject
  wsgi = true
  eggs =
    ${buildout:eggs}
  test =
    someapp
    anotherapp

Example using .pth files
========================

Pinax uses a .pth file to add a bunch of libraries to its path; we can
specify it's directory to get the libraries it specified added to our
path::

  [buildout]
  parts	= PIL
	  svncode
	  myproject
  versions=versions

  [versions]
  django	= 1.3

  [PIL]
  recipe	= zc.recipe.egg:custom
  egg		= PIL
  find-links	= http://dist.repoze.org/

  [svncode]
  recipe	= iw.recipe.subversion
  urls		= http://svn.pinaxproject.com/pinax/tags/0.5.1rc1	pinax

  [myproject]
  recipe	= djangorecipe
  eggs		=
    PIL
  project	= myproject
  settings	= settings
  extra-paths	= ${buildout:directory}/myproject/apps
		  ${svncode:location}/pinax/apps/external_apps
		  ${svncode:location}/pinax/apps/local_apps
  pth-files	= ${svncode:location}/pinax/libs/external_libs
  wsgi		= true

Above, we use stock Pinax for pth-files and extra-paths paths for
apps, and our own project for the path that will be found first in the
list.  Note that we expect our project to be checked out (e.g., by
svn:external) directly under this directory in to 'myproject'.

Example with a different Python version
=======================================

To use a different Python version from the one that ran buildout in the
generated script use something like::

  [buildout]
  parts	= myproject

  [special-python]
  executable = /some/special/python

  [myproject]
  recipe	= djangorecipe
  project	= myproject
  python	= special-python

Example configuration for mod_wsgi
==================================

If you want to deploy a project using mod_wsgi you could use this
example as a starting point::

  <Directory /path/to/buildout>
         Order deny,allow
         Allow from all
  </Directory>
  <VirtualHost 1.2.3.4:80>
         ServerName      my.rocking.server
         CustomLog       /var/log/apache2/my.rocking.server/access.log combined
         ErrorLog        /var/log/apache2/my.rocking.server/error.log
         WSGIScriptAlias / /path/to/buildout/bin/django.wsgi
  </VirtualHost>
