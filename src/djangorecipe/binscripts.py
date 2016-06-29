import os
import sys

from django.core import management


def manage(settings_file):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
    management.execute_from_command_line(sys.argv)


def test(settings_file, coverage_functions, *apps):
    optional_arguments = sys.argv[1:]
    sys.argv[1:] = ['test'] + list(apps) + optional_arguments
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
    if coverage_functions:
        import coverage
        cov = coverage.coverage()
        cov.erase()
        cov.start()

    management.execute_from_command_line(sys.argv)

    if coverage_functions:
        cov.stop()
        cov.save()
        # coverage_functions will be something like "report xml_report", which
        # means we have to call ``cov.report()`` and ``cov.xml_report()``.
        function_names = coverage_functions.split()
        for function_name in function_names:
            getattr(cov, function_name)()


def wsgi(settings_file, logfile=None):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
    if logfile:
        import datetime

        class logger(object):
            def __init__(self, logfile):
                self.logfile = logfile

            def write(self, data):
                self.log(data)

            def writeline(self, data):
                self.log(data)

            def log(self, msg):
                line = '%s - %s\n' % (
                    datetime.datetime.now().strftime('%Y%m%d %H:%M:%S'), msg)
                fp = open(self.logfile, 'a')
                try:
                    fp.write(line)
                finally:
                    fp.close()
        sys.stdout = sys.stderr = logger(logfile)

    # Run WSGI handler for the application
    from django.core.wsgi import get_wsgi_application
    return get_wsgi_application()
