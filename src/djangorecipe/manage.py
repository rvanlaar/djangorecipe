import os
import sys

import django
from django.core import management

def main_pre_14(settings_file):
    try:
        mod = __import__(settings_file)
        components = settings_file.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
    except ImportError:
        # XXX: Hack for python < 2.6
        _, e, _ = sys.exc_info()
        sys.stderr.write("Error loading the settings module '%s': %s"
                            % (settings_file, e))
        sys.exit(1)
    management.execute_manager(mod)


def main_14(settings_file):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
    management.execute_from_command_line(sys.argv)


def main(settings_file):
    if django.VERSION[0:2] >= (1, 4):
        main_14(settings_file)
    else:
        main_pre_14(settings_file)
