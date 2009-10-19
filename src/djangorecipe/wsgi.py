import sys

from django.core import management

def main(settings_file, logfile=None):
    try:
        mod = __import__(settings_file)
        components = settings_file.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)

    except ImportError, e:
        sys.stderr.write("Error loading the settings module '%s': %s"
                            % (settings_file, e))
        sys.exit(1)

    # Setup settings
    management.setup_environ(mod)

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

    from django.core.handlers.wsgi import WSGIHandler

    # Run WSGI handler for the application
    return WSGIHandler()
