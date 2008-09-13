from random import choice
import os
import subprocess
import urllib
import shutil
import logging

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
        self.log = logging.getLogger(name)
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
        # set this so the rest of the recipe can expect it to be there
        options.setdefault('pythonpath', '')

        # Usefull when using archived versions
        buildout['buildout'].setdefault(
            'download-cache',
            os.path.join(buildout['buildout']['directory'], 
                         'downloads'))

        # mod_wsgi support script
        options.setdefault('wsgi', 'false')

        # only try to download stuff if we aren't asked to install from cache
        self.install_from_cache = self.buildout['buildout'].get(
            'install-from-cache', '').strip() == 'true'


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
            
        if self.is_svn_url(version):
            self.install_svn_version(version, download_dir, location, 
                                     self.install_from_cache)
        else:
            tarball = self.get_release(version, download_dir)
            # Extract and put the dir in its proper place
            self.install_release(version, download_dir, tarball, location)

        requirements, ws = self.egg.working_set()
        ws_locations = [d.location for d in ws]

        extra_paths = [os.path.join(location), base_dir]
        extra_paths.extend(ws_locations)

        pythonpath = [p.replace('/', os.path.sep) for p in
                      self.options['pythonpath'].splitlines() if p.strip()]
        extra_paths.extend(pythonpath)
        
        requirements, ws = self.egg.working_set(['djangorecipe'])

        # Create the Django management script
        self.create_manage_script(extra_paths, ws)

        # Create the test runner
        self.create_test_runner(extra_paths, ws)

        # Make the wsgi script if enabled
        if self.options.get('wsgi').lower() == 'true':
            self.make_wsgi_script(extra_paths)


        # Create default settings if we haven't got a project
        # egg specified, and if it doesn't already exist
        if not self.options.get('projectegg'):
            if not os.path.exists(project_dir):
                self.create_project(project_dir)
            else:
                self.log.info('Skipping creating of project: %(project)s since it exists' % self.options)

        return location

    def install_svn_version(self, version, download_dir, location, 
                            install_from_cache):
        svn_url = self.version_to_svn(version)
        download_location = os.path.join(
            download_dir, 'django-' + 
            self.version_to_download_suffix(version))
        if not install_from_cache:
            if os.path.exists(download_location):
                if self.svn_update(download_location, version):
                    raise UserError(
                        "Failed to update Django; %s. "
                        "Please check your internet connection." % (
                            download_location))
            else:
                self.log.info("Checking out Django from svn: %s" % svn_url)
                if self.command('svn co %s %s' % (svn_url, download_location)):
                    raise UserError("Failed to checkout Django. "
                                    "Please check your internet connection.")
        else:
            self.log.info("Installing Django from cache: " + download_location)

        shutil.copytree(download_location, location)


    def install_release(self, version, download_dir, tarball, destination):
        extraction_dir = os.path.join(download_dir, 'django-archive')
        setuptools.archive_util.unpack_archive(tarball, extraction_dir)
        # Lookup the resulting extraction dir instead of guessing it
        # (Django releases have a tendency not to be consistend here)
        untarred_dir = os.path.join(extraction_dir, 
                                    os.listdir(extraction_dir)[0])
        shutil.move(untarred_dir, destination)
        shutil.rmtree(extraction_dir)

    def get_release(self, version, download_dir):
        tarball = os.path.join(download_dir, 'django-%s.tar.gz' % version)
            
        # Only download when we don't yet have an archive
        if not os.path.exists(tarball):
            download_url = 'http://www.djangoproject.com/download/%s/tarball/'
            self.log.info("Downloading Django from: %s" % download_url)
            urllib.urlretrieve(download_url % version, tarball)
        return tarball

    def create_manage_script(self, extra_paths, ws):
        project = self.options.get('projectegg', self.options['project'])
        zc.buildout.easy_install.scripts(
            [(self.options.get('control-script', self.name),
              'djangorecipe.manage', 'main')],
            ws, self.options['executable'], self.options['bin-directory'],
            extra_paths = extra_paths,
            arguments= "'%s.%s'" % (project, 
                                    self.options['settings']))



    def create_test_runner(self, extra_paths, working_set):
        apps = self.options.get('test', '').split()
        # Only create the testrunner if the user requests it
        if apps:
            zc.buildout.easy_install.scripts(
                [(self.options.get('testrunner', 'test'),
                  'djangorecipe.test', 'main')],
                working_set, self.options['executable'], 
                self.options['bin-directory'],
                extra_paths = extra_paths,
                arguments= "'%s.%s', %s" % (
                    self.options['project'],
                    self.options['settings'],
                    ', '.join(["'%s'" % app for app in apps])))


    def create_project(self, project_dir):
        os.makedirs(project_dir)

        template_vars = {'secret': self.generate_secret()}
        template_vars.update(self.options)

        self.create_file(
            os.path.join(project_dir, 'development.py'),
            development_settings, template_vars)

        self.create_file(
            os.path.join(project_dir, 'production.py'),
            production_settings, template_vars)

        self.create_file(
            os.path.join(project_dir, 'urls.py'),
            urls_template, template_vars)

        self.create_file(
            os.path.join(project_dir, 'settings.py'),
            settings_template, template_vars)

        # Create the media and templates directories for our
        # project
        os.mkdir(os.path.join(project_dir, 'media'))
        os.mkdir(os.path.join(project_dir, 'templates'))

        # Make the settings dir a Python package so that Django
        # can load the settings from it. It will act like the
        # project dir.
        open(os.path.join(project_dir, '__init__.py'), 'w').close()


    def make_wsgi_script(self, extra_paths):
        script_name = os.path.join(
            self.buildout['buildout']['bin-directory'],
            self.options.get('control-script', self.name) + '.wsgi')
        f = open(script_name, 'w')
        o = {'extra_paths': repr(extra_paths)}
        o.update(self.options)
        if self.options.get('projectegg'):
            o['project'] = self.options.get('projectegg')
        f.write(wsgi_template % o)
        f.close()

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

    def svn_update(self, path, version):
        command = 'svn up'
        if '@' in self.options['version']:
            command += ' -r ' + version.split('@')[-1]
        self.log.info("Updating Django from svn")
        return self.command(command, cwd=path)

    def update(self):
        if not self.install_from_cache and \
                self.is_svn_url(self.options['version']):
            self.svn_update(self.options['location'], self.options['version'])

    def command(self, cmd, **kwargs):
        output = subprocess.PIPE
        if self.buildout['buildout'].get('verbosity'):
            output = None
        command = subprocess.Popen(
            cmd, shell=True, stdout=output, **kwargs)
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

