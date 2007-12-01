from django.core.management import execute_manager

def main(settings_file):
    try:
        settings = __import__(settings_file)
    except ImportError:
        import sys
        sys.stderr.write("Error: Can't load the file 'settings.py'")
        sys.exit(1)

    execute_manager(settings)
