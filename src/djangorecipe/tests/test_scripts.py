import sys
import unittest

import mock


class ScriptTestCase(unittest.TestCase):

    def setUp(self):
        # We will also need to fake the settings file's module
        self.settings = mock.sentinel.Settings
        #self.settings.SECRET_KEY = 'I mock your secret key'
        sys.modules['cheeseshop'] = mock.sentinel.CheeseShop
        sys.modules['cheeseshop.development'] = self.settings
        sys.modules['cheeseshop'].development = self.settings

    def tearDown(self):
        # We will clear out sys.modules again to clean up
        for m in ['cheeseshop', 'cheeseshop.development']:
            del sys.modules[m]

    def check_settings_error(self, module):
        # When the settings file cannot be imported the management
        # script will exit with a message and a specific exit code.
        self.assertRaises(ImportError, module.main, 'cheeseshop.tilsit')


class TestTestScript(ScriptTestCase):

    @mock.patch('django.core.management.execute_from_command_line')
    @mock.patch('os.environ.setdefault')
    def test_script(self, mock_setdefault, execute_from_command_line):
        # The test script should execute the standard Django test
        # command with any apps given as its arguments.
        from djangorecipe import test
        test.main('cheeseshop.development',  'spamm', 'eggs')
        # We only care about the arguments given to execute_from_command_line
        self.assertEqual(execute_from_command_line.call_args[0],
                         (['test', 'test', 'spamm', 'eggs'],))
        self.assertEqual(mock_setdefault.call_args[0],
                         ('DJANGO_SETTINGS_MODULE', 'cheeseshop.development'))

    @mock.patch('django.core.management.execute_from_command_line')
    @mock.patch('os.environ.setdefault')
    def test_deeply_nested_settings(self, mock_setdefault, execute_from_command_line):
        # Settings files can be more than two levels deep. We need to
        # make sure the test script can properly import those. To
        # demonstrate this we need to add another level to our
        # sys.modules entries.
        settings = mock.sentinel.SettingsModule
        settings.SECRET_KEY = 'I mock your secret key'
        nce = mock.sentinel.NCE
        nce.development = settings
        sys.modules['cheeseshop'].nce = nce
        sys.modules['cheeseshop.nce'] = nce
        sys.modules['cheeseshop.nce.development'] = settings
        from djangorecipe import test
        test.main('cheeseshop.nce.development',  'tilsit', 'stilton')
        self.assertEqual(mock_setdefault.call_args[0],
                         ('DJANGO_SETTINGS_MODULE', 'cheeseshop.nce.development'))

    def test_settings_error(self):
        from djangorecipe import test
        self.check_settings_error(test)


class TestManageScript(ScriptTestCase):

    @mock.patch('django.core.management.execute_from_command_line')
    @mock.patch('os.environ.setdefault')
    def test_script(self, mock_setdefault, mock_execute):
        # The manage script is a replacement for the default manage.py
        # script. It has all the same bells and whistles since all it
        # does is call the normal Django stuff.
        from djangorecipe import manage
        manage.main('cheeseshop.development')
        self.assertEqual(mock_execute.call_args,
                         ((sys.argv,), {}))
        self.assertEqual(
            mock_setdefault.call_args,
            (('DJANGO_SETTINGS_MODULE', 'cheeseshop.development'), {}))


class TestWSGIScript(ScriptTestCase):

    @mock.patch('django.core.management.setup_environ')
    @mock.patch('django.core.handlers.wsgi.WSGIHandler')
    def test_script(self, WSGIHandler, setup_environ):
        # The wsgi is a wrapper for the django wsgi script.
        from djangorecipe import wsgi
        wsgi.main('cheeseshop.development', logfile=None)
        self.assertEqual(WSGIHandler.call_args, {})

    # Skipping because returning the wsgi runner
    # def test_settings_error(self):
    #     from djangorecipe import wsgi
    #     self.check_settings_error(wsgi)
