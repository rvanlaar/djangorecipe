import os
import sys

from django.core import management


def main(settings_file, *apps):
    optional_arguments = sys.argv[1:]
    sys.argv[1:] = ['test'] + list(apps) + optional_arguments
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
    management.execute_from_command_line(sys.argv)
