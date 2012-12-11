from django.core import management


def main(settings_file, logfile=None):
    try:
        mod = __import__(settings_file)
        components = settings_file.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)

    except ImportError:
        import sys
        # XXX: Hack for python < 2.6
        _, e, _ = sys.exc_info()
        sys.stderr.write("Error loading the settings module '%s': %s"
                         % (settings_file, e))
        sys.exit(1)

    # Setup settings
    management.setup_environ(mod)

    from django.conf import settings

    options = getattr(settings, 'FCGI_OPTIONS', {})
    if logfile:
        options['outlog'] = logfile
        options['errlog'] = logfile

    from django.core.servers.fastcgi import runfastcgi

    # Run FASTCGI handler
    runfastcgi(**options)
