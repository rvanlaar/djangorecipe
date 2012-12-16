import sys
import unittest

import mock


class ScriptTestCase(unittest.TestCase):

    def setUp(self):
        # We will also need to fake the settings file's module
        self.settings = mock.sentinel.Settings
        sys.modules['cheeseshop'] = mock.sentinel.CheeseShop
        sys.modules['cheeseshop.development'] = self.settings
        sys.modules['cheeseshop'].development = self.settings

    def tearDown(self):
        # We will clear out sys.modules again to clean up
        for m in ['cheeseshop', 'cheeseshop.development']:
            del sys.modules[m]

    @mock.patch('sys.stderr')
    @mock.patch('sys.exit')
    def check_settings_error(self, module, sys_exit, stderr):
        # When the settings file cannot be imported the management
        # script it wil exit with a message and a specific exit code.
        self.assertRaises(UnboundLocalError, module.main, 'cheeseshop.tilsit')
        self.assertEqual(stderr.write.call_args,
                         (("Error loading the settings module "
                           "'cheeseshop.tilsit': "
                           "No module named tilsit",), {}))
        self.assertEqual(sys_exit.call_args, ((1,), {}))


class TestTestScript(ScriptTestCase):

    @mock.patch('django.core.management.execute_manager')
    def test_script(self, execute_manager):
        # The test script should execute the standard Django test
        # command with any apps given as its arguments.
        from djangorecipe import test
        test.main('cheeseshop.development',  'spamm', 'eggs')
        # We only care about the arguments given to execute_manager
        self.assertEqual(execute_manager.call_args[1],
                         {'argv': ['test', 'test', 'spamm', 'eggs']})

    @mock.patch('django.core.management.execute_manager')
    def test_deeply_nested_settings(self, execute_manager):
        # Settings files can be more than two levels deep. We need to
        # make sure the test script can properly import those. To
        # demonstrate this we need to add another level to our
        # sys.modules entries.
        settings = mock.sentinel.SettingsModule
        nce = mock.sentinel.NCE
        nce.development = settings
        sys.modules['cheeseshop'].nce = nce
        sys.modules['cheeseshop.nce'] = nce
        sys.modules['cheeseshop.nce.development'] = settings
        from djangorecipe import test
        test.main('cheeseshop.nce.development',  'tilsit', 'stilton')
        self.assertEqual(execute_manager.call_args[0], (settings,))

    def test_settings_error(self):
        from djangorecipe import test
        self.check_settings_error(test)


class TestManageScript(ScriptTestCase):

    @mock.patch('django.core.management.execute_manager')
    def test_script_pre_14(self, execute_manager):
        # The manage script is a replacement for the default manage.py
        # script. It has all the same bells and whistles since all it
        # does is call the normal Django stuff.
        from djangorecipe import manage
        manage.main_pre_14('cheeseshop.development')
        self.assertEqual(execute_manager.call_args,
                         ((self.settings,), {}))

    @mock.patch('django.core.management.execute_from_command_line')
    @mock.patch('os.environ.setdefault')
    def test_script_14(self, mock_setdefault, mock_execute):
        # The manage script is a replacement for the default manage.py
        # script. It has all the same bells and whistles since all it
        # does is call the normal Django stuff.
        from djangorecipe import manage
        manage.main_14('cheeseshop.development')
        self.assertEqual(mock_execute.call_args,
                         ((sys.argv,), {}))
        self.assertEqual(
            mock_setdefault.call_args,
            (('DJANGO_SETTINGS_MODULE', 'cheeseshop.development'), {}))

    @mock.patch('djangorecipe.manage.main_pre_14')
    @mock.patch('djangorecipe.manage.main_14')
    @mock.patch('django.VERSION', new=(1, 3, 0))
    def test_django_pre_13_selection(self, mock_14, mock_pre_14):
        from djangorecipe import manage
        manage.main('cheeseshop.development')
        self.assertTrue(mock_pre_14.called)
        self.assertFalse(mock_14.called)

    @mock.patch('djangorecipe.manage.main_pre_14')
    @mock.patch('djangorecipe.manage.main_14')
    @mock.patch('django.VERSION', new=(1, 4, 0))
    def test_django_pre_14_selection(self, mock_14, mock_pre_14):
        from djangorecipe import manage
        manage.main('cheeseshop.development')
        self.assertTrue(mock_14.called)
        self.assertFalse(mock_pre_14.called)

    def test_settings_error_pre_14(self):
        from djangorecipe import manage
        manage.main = manage.main_pre_14
        # ^^^ patch main; check_settings_errors calls main.
        self.check_settings_error(manage)


class TestFCGIScript(ScriptTestCase):

    @mock.patch('django.conf.settings')
    @mock.patch('django.core.management.setup_environ')
    @mock.patch('django.core.servers.fastcgi.runfastcgi')
    def test_script(self, runfastcgi, setup_environ, settings):
        # The fcgi is a wrapper for the django fcgi script.
        from djangorecipe import fcgi
        settings.FCGI_OPTIONS = {}
        fcgi.main('cheeseshop.development', logfile=None)
        self.assertEqual(setup_environ.call_args,
                         ((self.settings,), {}))
        self.assertEqual(runfastcgi.call_args, {})

    def test_settings_error(self):
        from djangorecipe import fcgi
        self.check_settings_error(fcgi)


class TestWSGIScript(ScriptTestCase):

    @mock.patch('django.core.management.setup_environ')
    @mock.patch('django.core.handlers.wsgi.WSGIHandler')
    def test_script(self, WSGIHandler, setup_environ):
        # The wsgi is a wrapper for the django wsgi script.
        from djangorecipe import wsgi
        wsgi.main('cheeseshop.development', logfile=None)
        self.assertEqual(WSGIHandler.call_args, {})

    def test_settings_error(self):
        from djangorecipe import wsgi
        self.check_settings_error(wsgi)
