from django.core import management

def main(settings_file):
    try:
        mod = __import__(settings_file)
        components = settings_file.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)

    except ImportError:
        import sys
        sys.stderr.write("Error: Can't load the file 'settings.py'")
        return sys.exit(1)

    management.execute_manager(mod)
