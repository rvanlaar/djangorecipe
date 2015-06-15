Changes
=======


2.1 (2015-06-15)
----------------

- Renamed ``script-entrypoints`` option to ``scripts-with-settings``. It
  accepts script names that would otherwise get generated (like ``gunicorn``)
  and generates a duplicate script named like ``bin/gunicorn-with-settings``.

  Technical note: this depends on the scripts being setuptools "console_script
  entrypoint" scripts.


2.0 (2015-06-10)
----------------

- Removed project generation. Previously, djangorecipe would generate a
  directory for you from a template, but Django's own template is more than
  good enough now. Especially: it generates a subdirectory for your project
  now. Just run ``bin/django startproject <projectname>``.

  See django's documentation for `startproject
  <https://docs.djangoproject.com/en/1.8/ref/django-admin/#django-admin-startproject>`_.

  You can also look at `cookiecutter <https://cookiecutter.readthedocs.org/>`_.

  This also means the ``projectegg`` option is now deprecated, it isn't needed
  anymore.

- We aim at django 1.7 and 1.8 now. Django 1.4 still works, (except that that
  one doesn't have a good startproject command).

- Gunicorn doesn't come with the django manage.py integration, so ``bin/django
  run_gunicorn`` doesn't work anymore. If you add ``script-entrypoints =
  gunicorn`` to the configuration, we generate a ``bin/django_env_gunicorn``
  script that is identical to ``bin/gunicorn``, only with the environment
  correctly set.  **Note: renamed in 2.1 to ``scripts-with-settings``**.

  This way, you can use the wsgi.py script in your project (copy it from the
  django docs if needed) with ``bin/django_env_gunicorn yourproject/wsgi.py``
  just like suggested everywhere. This way you can adjust your wsgi file to
  your liking and run it with gunicorn.

  For other wsgi runners (or programs you want to use with the correct
  environment set), you can add a full entry point to ``script-entrypoints``,
  like ``script-entrypoints = gunicorn=gunicorn.app.wsgiapp:run`` would be the
  full line for gunicorn. Look up the correct entrypoint in the relevant
  package's ``setup.py``.

  Django's 1.8 ``wsgi.py`` file looks like this, see https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/::

      import os

      from django.core.wsgi import get_wsgi_application

      os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yourproject.settings")

      application = get_wsgi_application()


- The ``wsgilog`` option has been deprecated, the old apache mod_wsgi script
  hasn't been used for a long time.

- Removed old pth option, previously used for pinax. Pinax uses proper python
  packages since a long time, so it isn't needed anymore.



1.11 (2014-11-21)
-----------------

- The ``dotted-settings-path`` options was only used in management script. Now
  it is also used for the generated wsgi file and the test scripts.


1.10 (2014-06-16)
-----------------

- Added ``dotted-settings-path`` option. Useful when you want to specify a
  custom settings path to be used by the ``manage.main()`` command.

- Renamed ``deploy_script_extra`` (with underscores) to
  ``deploy-script-extra`` (with dashes) for consistency with the other
  options. If the underscore version is found, an exception is raised.


1.9 (2014-05-27)
----------------

- ``bin/test`` now passes along command line arguments to the underlying
  management command. Previously, only the equivalent of ``manage.py test
  list_of_apps`` would be done. Now command line arguments are passed as-is
  after the list of apps.

- Added ``deploy_script_extra`` option. It is appended to the wsgi script.
  Useful for instance for a cloud hoster where you need to wrap your wsgi
  application object in a custom call.


1.8 (2014-05-27)
----------------

- Supporting buildout's relative-paths setting now.


1.7 (2013-12-11)
----------------

- Add option to change the wsgi script name. Thanks hedleyroos (Fixes pull #74)

1.6 (2013-10-28)
----------------

- Djangorecipe works with django 1.6 now.

- Tested with Django 1.4, 1.5 and 1.6. Pre-1.4 support is gone, now. Also
  tested on Python 2.6/2.7, 3.2/3.3.

- Moved to buildout 2 support only.

- Removed generation of fastcgi script. You can run it easily as ``bin/django
  runfcgi`` and it will be deprecated in Django 1.7 anyway.


1.5 (2013-01-25)
----------------

- Removed support for a different python version than the one you use to run
  buildout with. Previously, you could run your buildout with 2.6 but get
  Django to use 2.7 instead. zc.buildout 2.0 doesn't allow it anymore, so we
  removed it too.


1.4 (2013-01-15)
----------------

- Added initialization code support. Thanks to anshumanb, jjmurre. (Closes #58).


1.3 (2012-09-07)
----------------

- Removed deprecation warning in Django 1.4. Fixes #49, thanks Shagi.

- Added documentation for use with mr.developer. Thanks shagi (closes issue #45)

- Added Travis support.


1.2.1 (2012-05-15)
------------------

- Fixed broken 1.2 release (missing ``*.rst`` files due to a recent txt-to-rst
  rename action).


1.2 (2012-05-14)
----------------

- Removed location path from recipe. Thanks bleskes (fixes issue #50).

1.1.2
-----

- Added correct url to the deprecation warning

1.1.1
-----

- Fixed Python3 Trove classifiers

1.1
---

- Support python3.
- Changed buildout and the tests to run the tests under nose.
- Removed some old pre 0.99 unittests that dealt with download support.

1.0
---

- Stable release with a real 1.0 version.
- Made djangorecipe more pep08 compliant.

0.99
----

- Djangorecipe now depends on Django. The use of the `version =` statement
  is deprecated. Specify the django version in the
  `[versions]` section. Install django via mr.developer if you need to use
  an svn/git/hg repository. For other uses
  Versionpin djangorecipe to 0.23.1 if you don't want to upgrade.
  Thanks to Reinout van Rees for help with this release.

- Removed subversion and download support.

0.23.1
------

- Added a missing 'import os'

0.23
----

- Support for settings/urls boilerplate for django 1.2 and django 1.3.
  It defaults to 1.3 when the version isn't 1.2.

0.22
----

- Added support for svn urls with spaces. Thanks to Brad103 (fixes #537718).

- Updated code and buildout to use newest zc.recipe.egg,
  zc.recipe.testrunner and python-dateutil.

0.21
----

- The admin url is now configured for django 1.1 or higher. Thanks to
  Sam Charrington (fixes #672220).

- Bootstrap.py updated (fixes #501954).

0.20
----

- The recipe know makes the `django` package know to setuptools during install.
  This closes #397864. Thanks to Daniel Bruce and Dan Fairs for the patch.

- Fixed #451065 which fixes a problem with the WSGI log file option.

- Added the posibilty to configure more FCGI related settings. Thanks to Vasily
  Sulatskov for the patch.

0.19.2
------

- The generated WSGI & FCGI scripts are now properly removed when
  options change (fixes #328182). Thanks to Horst Gutmann for the
  patch.

- Scripts are now updated when dependencies change. This fixes #44658,
  thanks to Paul Carduner for the patch.

0.19.1
------

- Applied fix for the change in WSGI script generation. The previous
  release did not work properly.

0.19
----

- When running again with non-newest set the recipe will no longer
  update the Subversion checkout. Thanks to vinilios for the patch.

- The WSGI and FCGI scripts are now generated using Buildout's own
  system. This makes them more similar to the generated manage script
  with regard to the setup of paths. Thanks to Jannis Leidel for the
  patch.

0.18
----

- Paths from eggs and extra-paths now get precedence over the default
  system path (fixes #370420). Thanks to Horst Gutmann for the patch.

- The generated WSGI script now uses the `python` option if
  present. This fixes #361695.

0.17.4
------

- Fixed a problem when not running in verbose mode (fixes #375151).

0.17.3
------

- Removed dependency on setuptools_bzr since it does not seem to work
  like I expected.

0.17.2
------

- Changed the download code to use urllib2. This should make it work
  from behind proxies (fixes #362822). Thanks to pauld for the patch.

0.17.1
------

- Fixed a problem with the new WSGI logging option #348797. Thanks to
  Bertrand Mathieu for the patch.

- Disable generation of the WSGI log if "wsgilog" isn't set, thanks to
  Jacob Kaplan-Moss for the patch.

- Updated buildout.cfg and .bzrignore, thanks Jacob Kaplan-Moss.

0.17
----

- Added an option to specify a log file for output redirection from
  the WSGI script. Thanks to Guido Wesdorp for the patch.

0.16
----

- Subversion aliases are now supported (something like
  svn+mystuff://myjunk). Thanks to Remco for the patch.

0.15.2
------

- Update to move pth-files finder from the __init__ method to the
  install method so it runs in buildout-order, else it looks for pth
  files in dirs that may not yet exist. Thanks to Chris Shenton for
  the update to his original patch.

0.15.1
------

- Update to make the previously added pth-files option better
  documented.

0.15
----

- Added "pth-files" option to add libraries to extra-paths from
  site .pth files. Thanks to Chris Shenton for the patch.

0.14
----

- The recipe now supports creating a FCGI script. Thanks to Jannis
  Leidel for the patch.

- When downloading a Django recipe for the first time the recipe now
  properly reports the url it is downloading from.

0.13
----

- Specifying a user name within a subversion url now works. The code
  that determined the revision has been updated. This fixes issue
  #274004. Thanks to Remco for the patch.

- Updated the template for creating new projects. It now uses the
  current admin system when generating it's `urls.py` file. This fixes
  issue #276255. Thanks to Roland for the patch.

0.12.1
------

- Re-upload since CHANGES.txt was missing from the release

0.12
----

- The recipe no longer executes subversion to determine whether the
  versions is to be downloaded using subversion. This fixes issue
  #271145. Thanks to Kapil Thangavelu for the patch.

- Changed the `pythonpath` option to `extra-paths`. This makes the
  recipe more consistent with other recipes (see issue #270908).

0.11
----

- Another go at fixing the updating problem (#250811) by making sure
  the update method is always called. It would not be called in the
  previous version since the recipe wrote a random secret (if it
  wasn't specified) to the options for use with a template. Buildout
  saw this as a change in options and therefore always decided to
  un-install & install.

- When both projectegg and wsgi=True are specified, the generated wsgi
  file did not have the correct settings file in it. This has been
  fixed with a patch from Dan Fairs.

- The recipe now has logging. All print statements have been replaced
  and a few extra logging calls have been added. This makes the recipe
  more informative about long running tasks. Thanks erny for the patch
  from issue #260628.

0.10
----

- The recipe no longer expects the top level directory name in a
  release tarball to be consistent with the version number. This fixes
  issue #260097. Thanks to erny for reporting this issue and
  suggesting a solution.

- Revision pinns for the svn checkout now stay pinned when re-running
  the buildout. This fixes issue #250811. Thanks to Remco for
  reporting this.

- Added an option to specify an egg to use as the project. This
  disables the code which creates the basic project structure. Thanks
  to Dan Fairs for the patch from issue #252647.

0.9.1
-----

- Fixed the previous release which was broken due to a missing
  manifest file

0.9
---

- The settings option is fixed so that it supports arbitrary depth
  settings paths (example; `conf.customer.development`).

- The version argument now excepts a full svn url as well. You can use
  this to get a branch or fix any url to a specific revision with the
  standard svn @ syntax

- The wsgi script is no longer made executable and readable only by
  the user who ran buildout. This avoids problems with deployment.
