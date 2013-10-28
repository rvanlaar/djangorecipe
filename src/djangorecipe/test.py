import os

from django.core import management


def main(settings_file, *apps):
    argv = ['test', 'test'] + list(apps)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
    management.execute_from_command_line(argv)
