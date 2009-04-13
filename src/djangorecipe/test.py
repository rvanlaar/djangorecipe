from django.core import management

def main(settings_file, *apps):
    argv = ['test', 'test'] + list(apps)
    try:
        settings = __import__(settings_file)
        components = settings_file.split('.')
        for comp in components[1:]:
            settings = getattr(settings, comp)
    except ImportError, e:
        import sys
        sys.stderr.write("Error loading the settings module '%s': %s"
                            % (settings_file, e))
        return sys.exit(1)

    management.execute_manager(settings, argv=argv)
