from random import choice
import os
import subprocess
from zc.buildout import UserError
import zc.recipe.egg
import urllib
import setuptools
import shutil

settings_template = '''
import os

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '%(media_root)s'

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

development_settings = settings_template + '''
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

class Recipe(object):
    def __init__(self, buildout, name, options):
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        self.buildout, self.name, self.options = buildout, name, options
        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'], name)
        options['bin-directory'] = buildout['buildout']['bin-directory']

        options.setdefault('project', 'project')
        options.setdefault('settings', 'development')


        options.setdefault('urlconf', 'urls')
        options.setdefault(
            'media_root', os.path.abspath(os.path.join(
                    os.path.dirname(__file__), 'media')))
        options.setdefault('secret', self.generate_secret())
        # set this so the rest of the recipe can expect it to be there
        options.setdefault('pythonpath', '')

        # Usefull when using archived versions
        buildout['buildout'].setdefault(
            'download-directory',
            os.path.join(buildout['buildout']['directory'], 
                         'downloads'))


    def install(self):
        location = self.options['location']
        base_dir = self.buildout['buildout']['directory']

        project_dir = os.path.join(base_dir, self.options['project'])

        download_dir = self.buildout['buildout']['download-directory']
        if not os.path.exists(download_dir):
            os.mkdir(download_dir)

        version = self.options['version']
        if version == 'trunk':
            download_location = os.path.join(download_dir, 'django-svn')
            if os.path.exists(download_location):
                if self.command('svn up %s' % download_location):
                    raise UserError(
                        "Failed to update Django; %s. "
                        "Please check your internet connection." % (
                            download_location))
                shutil.copytree(download_location, location)
            else:
                if self.command(
                    'svn co http://code.djangoproject.com/svn/django/trunk/ %s' % 
                    download_location):
                    raise UserError(
                        "Failed to checkout Django. "
                        "Please check your internet connection.")
        else:
            tarball = os.path.join(
                download_dir, 'django-%s.tar.gz' % version)
            extraction_dir = os.path.join(download_dir, 'django-archive')
            
            # Only download when we don't yet have an archive
            if not os.path.exists(tarball):
                download_url = 'http://www.djangoproject.com/download/%s/tarball/'
                urllib.urlretrieve(download_url % version, tarball)

            # Remove a pre-existing installation if it is there
            if os.path.exists(location):
                shutil.rmtree(location)
            
            # Extract and put the dir in its proper place
            untarred_dir = os.path.join(extraction_dir, 'Django-%s' % version)
            setuptools.archive_util.unpack_archive(tarball, extraction_dir)
            shutil.move(untarred_dir, location)
            shutil.rmtree(extraction_dir)

        requirements, ws = self.egg.working_set()
        ws_locations = [d.location for d in ws]

        extra_paths = [os.path.join(location), base_dir]
        extra_paths.extend(ws_locations)
        extra_paths.append(project_dir)

        pythonpath = [p.replace('/', os.path.sep) for p in
                      self.options['pythonpath'].splitlines() if p.strip()]
        extra_paths.extend(pythonpath)
        
        requirements, ws = self.egg.working_set(['djangorecipe'])

        zc.buildout.easy_install.scripts(
            [(self.options.get('control-script', self.name),
                'djangorecipe.manage', 'main')],
            ws, self.options['executable'], self.options['bin-directory'],
            extra_paths = extra_paths,
            arguments= "'settings'")

        # Create default settings
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        self.create_file(
            os.path.join(project_dir, 'development.py'),
            development_settings, self.options)

        self.create_file(
            os.path.join(project_dir, 'production.py'),
            settings_template, self.options)

        self.create_file(
            os.path.join(project_dir, 'urls.py'),
            urls_template, self.options)

        self.create_file(
            os.path.join(project_dir, 'settings.py'),
            'from %(project)s.%(settings)s import *', self.options)

        # Create the media and templates directories for our project
        os.mkdir(os.path.join(project_dir, 'media'))
        os.mkdir(os.path.join(project_dir, 'templates'))

        # Make the settings dir a Python package so that Django can
        # load the settings from it. It will act like the project dir.
        open(os.path.join(project_dir, '__init__.py'), 'w').close()

        return location

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

