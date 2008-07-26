from django.core import management

def main(settings_file, *apps):
    argv = ['test', 'test'] + list(apps)
    try:
        settings = __import__(settings_file)
        components = settings_file.split('.')
        for comp in components[1:]:
            settings = getattr(settings, comp)
    except ImportError:
        import sys
        sys.stderr.write("Error: Can't load the file 'settings.py'")
        return sys.exit(1)

    management.execute_manager(settings, argv=argv)
