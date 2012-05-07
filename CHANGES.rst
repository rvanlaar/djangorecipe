Changes
=======

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
