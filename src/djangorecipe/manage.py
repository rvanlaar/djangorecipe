import os
import sys

import django
from django.core import management


def main(settings_file):
    # First import the settings module. We need it for django < 1.4 and for
    # newer versions the warning if we can't find it is useful.
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

    if django.VERSION[0:2] >= (1, 4):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
        management.execute_from_command_line(sys.argv)
    else:
        # In Django 1.4, manage.py changed a bit.
        management.execute_manager(mod)
