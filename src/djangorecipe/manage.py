import os
import sys

from django.core import management


def main(settings_file):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
    management.execute_from_command_line(sys.argv)
