Description
===========

This buildout recipe can be used to create a setup for Django. It will
automatically download Django and install it in the buildout's
sandbox. You can use either a release version of Django or a
subversion checkout (by using `trunk` instead of a version number.

You can see an example of how to use the recipe below::

  [buildout]
  parts = satchmo django
  eggs = ipython
  
  [satchmo]
  recipe = gocept.download
  url = http://www.satchmoproject.com/snapshots/satchmo-0.6.tar.gz
  md5sum = 659a4845c1c731be5cfe29bfcc5d14b1
  
  [django]
  recipe = djangorecipe
  version = 0.96.1
  settings = development
  eggs = ${buildout:eggs}
  pythonpath = 
  ${satchmo:location}
  project = dummyshop


Supported options
=================

The recipe supports the following options.

project
  This option sets the name for your project. The recipe will create a
  basic structure if the project is not already there.

version
  The version argument can accept a few different types of
  arguments. You can specify `trunk`. In this case it will do a
  checkout of the Django trunk. Another option is to specify a release
  number like `0.96.2`. This will download the release
  tarball. Finally you can specify a full svn url (including the
  revision number). An example of this would be
  `http://code.djangoproject.com/svn/django/branches/newforms-admin@7833`.

settings
  You can set the name of the settings file which is to be used with
  this option. This is useful if you want to have a different
  production setup from your development setup. It defaults to
  `development`.

download-cache
  Set this to a folder somewhere on you system to speed up
  installation. The recipe will use this folder as a cache for a
  downloaded version of Django.

pythonpath
  All paths specified here will be used to extend the default Python
  path for the `bin/*` scripts.

control-script
  The name of the script created in the bin folder. This script is the
  equivalent of the `manage.py` Django normally creates. By default it
  uses the name of the section (the part between the `[ ]`).

wsgi
  An extra script is generated in the bin folder When this is set to
  `true`. This can be used with mod_wsgi to deploy the project. The
  name of the script is `control-script.wsgi`.

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
  version = trunk
  settings = development
  project = exampleproject
  wsgi = true
  eggs = 
    ${buildout:eggs}
  test = 
    someapp
    anotherapp


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
