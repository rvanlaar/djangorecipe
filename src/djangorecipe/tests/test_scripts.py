import os
import sys
import unittest

import mock

from djangorecipe import binscripts


class ScriptTestCase(unittest.TestCase):

    def setUp(self):
        # We will also need to fake the settings file's module
        self.settings = mock.sentinel.Settings
        self.settings.SECRET_KEY = 'I mock your secret key'
        sys.modules['cheeseshop'] = mock.sentinel.CheeseShop
        sys.modules['cheeseshop.development'] = self.settings
        sys.modules['cheeseshop'].development = self.settings
        print("DJANGO ENV: %s" % os.environ.get('DJANGO_SETTINGS_MODULE'))

    def tearDown(self):
        # We will clear out sys.modules again to clean up
        for m in ['cheeseshop', 'cheeseshop.development']:
            del sys.modules[m]


class TestTestScript(ScriptTestCase):

    @mock.patch('django.core.management.execute_from_command_line')
    @mock.patch('os.environ.setdefault')
    def test_script(self, mock_setdefault, execute_from_command_line):
        with mock.patch.object(sys, 'argv', ['bin/test']):
            # The test script should execute the standard Django test command
            # with any apps configured in djangorecipe given as its arguments.
            binscripts.test('cheeseshop.development',  'spamm', 'eggs')
            self.assertTrue(execute_from_command_line.called)
            self.assertEqual(execute_from_command_line.call_args[0],
                             (['bin/test', 'test', 'spamm', 'eggs'],))
            self.assertEqual(mock_setdefault.call_args[0],
                             ('DJANGO_SETTINGS_MODULE',
                              'cheeseshop.development'))

    @mock.patch('django.core.management.execute_from_command_line')
    @mock.patch('os.environ.setdefault')
    def test_script_with_args(self, mock_setdefault,
                              execute_from_command_line):
        with mock.patch.object(sys, 'argv', ['bin/test', '--verbose']):
            # The test script should execute the standard Django test command
            # with any apps given as its arguments. It should also pass along
            # command line arguments so that the actual test machinery can
            # pick them up (like '--verbose' or '--tests=xyz').
            binscripts.test('cheeseshop.development',  'spamm', 'eggs')
            self.assertEqual(
                execute_from_command_line.call_args[0],
                (['bin/test', 'test', 'spamm', 'eggs', '--verbose'],))
            self.assertEqual(
                mock_setdefault.call_args[0],
                ('DJANGO_SETTINGS_MODULE', 'cheeseshop.development'))

    @mock.patch('django.core.management.execute_from_command_line')
    @mock.patch('os.environ.setdefault')
    def test_deeply_nested_settings(self, mock_setdefault,
                                    execute_from_command_line):
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
        binscripts.test('cheeseshop.nce.development',  'tilsit', 'stilton')
        self.assertEqual(
            mock_setdefault.call_args[0],
            ('DJANGO_SETTINGS_MODULE', 'cheeseshop.nce.development'))


class TestManageScript(ScriptTestCase):

    @mock.patch('django.core.management.execute_from_command_line')
    @mock.patch('os.environ.setdefault')
    def test_script(self, mock_setdefault, mock_execute):
        # The manage script is a replacement for the default manage.py
        # script. It has all the same bells and whistles since all it
        # does is call the normal Django stuff.
        binscripts.manage('cheeseshop.development')
        self.assertEqual(mock_execute.call_args,
                         ((sys.argv,), {}))
        self.assertEqual(
            mock_setdefault.call_args,
            (('DJANGO_SETTINGS_MODULE', 'cheeseshop.development'), {}))


class TestWSGIScript(ScriptTestCase):
    # Note: don't test the logger part of wsgi(), because that overwrites
    # sys.stdout.

    def test_script(self):
        settings_dotted_path = 'cheeseshop.development'
        # ^^^ Our regular os.environ.setdefault patching doesn't help.
        # Patching get_wsgi_application already imports the DB layer, so the
        # settings are already needed there!
        with mock.patch('os.environ',
                        {'DJANGO_SETTINGS_MODULE': settings_dotted_path}):
            with mock.patch('django.core.wsgi.get_wsgi_application') \
                 as patched_method:
                binscripts.wsgi(settings_dotted_path, logfile=None)
                self.assertTrue(patched_method.called)
