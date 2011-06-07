Versions, VCS and Eggs
======================
The main focus of the development branch was the removal of the
subversion code and the start of using django eggs.
This is now implemented. Read on for some of the rational for this change.

Versions
--------

Version specifies a version, but is also magic.
It can be a django version number, an svn url or 'trunk', the django trunk.
It comes from the time that django didn't have a proper 1.0 release
and everybody used trunk or 0.9X.

VCS
---

Due to subversion support, there is a need for other version control
systems as well. There are different buildout recipes for there
systems. It's possible to drop subversion support when djangorecipe
uses eggs.

Eggs
----

Now Django is more mature other projects depend on Django being installed.
Djangorecipe install django in parts and as such it doesn't play nice
with the other projects that depend on Django. Using eggs deprecates
the download-cache option.

Other fixes
===========

Uninstall
---------

Add uninstall option to djangorecipe.
http://bazaar.launchpad.net/~jezdez/djangorecipe/djangorecipe-uninstall/revision/71

Add unicode support for README.
Jannis Leidel's talk.
