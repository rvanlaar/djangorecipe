from random import choice
import os
import stat
import subprocess
import urllib
import shutil

from zc.buildout import UserError
import zc.recipe.egg
import setuptools

settings_template = '''
import os

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = '%(project)s.db'
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = %(media_root)s

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Don't share this with anybody.
SECRET_KEY = '%(secret)s'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = '%(urlconf)s'


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), "templates"),
)


'''

production_settings = '''
from %(project)s.settings import *
'''

development_settings = '''
from %(project)s.settings import *
DEBUG=True
TEMPLATE_DEBUG=DEBUG
'''

urls_template = '''
from django.conf.urls.defaults import patterns, include, handler500
from django.conf import settings

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', 
         {'document_root': settings.MEDIA_ROOT}),
    )
'''

wsgi_template = '''
import os, sys
 
# Add the project to the python path
sys.path.extend(
  %(extra_paths)s
)
 
# Set our settings module
os.environ['DJANGO_SETTINGS_MODULE']='%(project)s.%(settings)s'
 
import django.core.handlers.wsgi
 
# Run WSGI handler for the application
application = django.core.handlers.wsgi.WSGIHandler()
'''

class Recipe(object):
    def __init__(self, buildout, name, options):
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        self.buildout, self.name, self.options = buildout, name, options
        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'], name)
        options['bin-directory'] = buildout['buildout']['bin-directory']

        options.setdefault('project', 'project')
        options.setdefault('settings', 'development')

        options.setdefault('urlconf', options['project'] + '.urls')
        options.setdefault(
            'media_root', 
            "os.path.join(os.path.dirname(__file__), 'media')")
        options.setdefault('secret', self.generate_secret())
        # set this so the rest of the recipe can expect it to be there
        options.setdefault('pythonpath', '')

        # Usefull when using archived versions
        buildout['buildout'].setdefault(
            'download-cache',
            os.path.join(buildout['buildout']['directory'], 
                         'downloads'))

        # mod_wsgi support script
        options.setdefault('wsgi', 'false')


    def install(self):
        location = self.options['location']
        base_dir = self.buildout['buildout']['directory']

        project_dir = os.path.join(base_dir, self.options['project'])

        download_dir = self.buildout['buildout']['download-cache']
        if not os.path.exists(download_dir):
            os.mkdir(download_dir)

        version = self.options['version']
        # Remove a pre-existing installation if it is there
        if os.path.exists(location):
            shutil.rmtree(location)
            
        # only try to download stuff if we aren't asked to install from cache
        install_from_cache = self.buildout['buildout'].get(
            'install-from-cache', '').strip() != 'true'

        if self.is_svn_url(version):
            svn_url = self.version_to_svn(version)
            download_location = os.path.join(
                download_dir, 'django-' + 
                self.version_to_download_suffix(version))
            if install_from_cache:
                if os.path.exists(download_location):
                    if self.command('svn up %s' % download_location):
                        raise UserError(
                            "Failed to update Django; %s. "
                            "Please check your internet connection." % (
                                download_location))
                else:
                    if self.command('svn co %s %s' % (svn_url, download_location)):
                        raise UserError(
                            "Failed to checkout Django. "
                            "Please check your internet connection.")
            else:
                print "Installing Django from cache: " + download_location

            shutil.copytree(download_location, location)
        else:
            tarball = os.path.join(
                download_dir, 'django-%s.tar.gz' % version)
            extraction_dir = os.path.join(download_dir, 'django-archive')
            
            # Only download when we don't yet have an archive
            if not os.path.exists(tarball):
                download_url = 'http://www.djangoproject.com/download/%s/tarball/'
                urllib.urlretrieve(download_url % version, tarball)

            # Extract and put the dir in its proper place
            untarred_dir = os.path.join(extraction_dir, 'Django-%s' % version)
            setuptools.archive_util.unpack_archive(tarball, extraction_dir)
            shutil.move(untarred_dir, location)
            shutil.rmtree(extraction_dir)

        requirements, ws = self.egg.working_set()
        ws_locations = [d.location for d in ws]

        extra_paths = [os.path.join(location), base_dir]
        extra_paths.extend(ws_locations)

        pythonpath = [p.replace('/', os.path.sep) for p in
                      self.options['pythonpath'].splitlines() if p.strip()]
        extra_paths.extend(pythonpath)
        
        requirements, ws = self.egg.working_set(['djangorecipe'])

        # Create the Django management script
        zc.buildout.easy_install.scripts(
            [(self.options.get('control-script', self.name),
                'djangorecipe.manage', 'main')],
            ws, self.options['executable'], self.options['bin-directory'],
            extra_paths = extra_paths,
            arguments= "'%s.%s'" % (self.options['project'], 
                                    self.options['settings']))

        # Create the test runner
        apps = self.options.get('test', '').split()
        # Only create the testrunner if the user requests it
        if apps:
            zc.buildout.easy_install.scripts(
                [(self.options.get('testrunner', 'test'),
                  'djangorecipe.test', 'main')],
                ws, self.options['executable'], self.options['bin-directory'],
                extra_paths = extra_paths,
                arguments= "'%s.%s', %s" % (
                    self.options['project'],
                    self.options['settings'],
                    ', '.join(["'%s'" % app for app in apps])))

        # Make the wsgi script if enabled
        if self.options.get('wsgi').lower() == 'true':
            script_name = os.path.join(base_dir, 'bin', self.options.get('control-script', self.name) + '.wsgi')
            f = open(script_name, 'w')
            o = {'extra_paths': repr(extra_paths)}
            o.update(self.options)
            f.write(wsgi_template % o)
            f.close()


        # Create default settings
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

            self.create_file(
                os.path.join(project_dir, 'development.py'),
                development_settings, self.options)

            self.create_file(
                os.path.join(project_dir, 'production.py'),
                production_settings, self.options)

            self.create_file(
                os.path.join(project_dir, 'urls.py'),
                urls_template, self.options)

            self.create_file(
                os.path.join(project_dir, 'settings.py'),
                settings_template, self.options)

            # Create the media and templates directories for our
            # project
            os.mkdir(os.path.join(project_dir, 'media'))
            os.mkdir(os.path.join(project_dir, 'templates'))

            # Make the settings dir a Python package so that Django
            # can load the settings from it. It will act like the
            # project dir.
            open(os.path.join(project_dir, '__init__.py'), 'w').close()
        else:
            print 'Skipping creating of project: %(project)s since it exists' % self.options

        return location

    def is_svn_url(self, version):
        return version == 'trunk' or subprocess.call(
            'svn info ' + version,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE) == 0

    def version_to_svn(self, version):
        if version == 'trunk':
            return 'http://code.djangoproject.com/svn/django/trunk/'
        else:
            return version

    def version_to_download_suffix(self, version):
        if version == 'trunk':
            return 'svn'
        return [p for p in version.split('/') if p][-1]

    def update(self):
        if self.options['version']:
            return

        subprocess.call('svn up %s' % self.options['location'], 
                        shell=True)

    def command(self, cmd):
        output = subprocess.PIPE
        if self.buildout['buildout'].get('verbosity'):
            output = None
        command = subprocess.Popen(
            cmd, shell=True, stdout=output)
        return command.wait()

    def create_file(self, file, template, options):
        if os.path.exists(file):
            return

        f = open(file, 'w')
        f.write(template % options)
        f.close()
        

    def generate_secret(self):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        return ''.join([choice(chars) for i in range(50)])

