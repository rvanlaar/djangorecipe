import unittest
import tempfile
import shutil
import os
import subprocess

import pkg_resources
import zc.buildout
from zc.buildout.buildout import Buildout

class TestRecipe(unittest.TestCase):
    def setUp(self):
        # ==================================
        # Taken/based on zc.buildout.testing
        # ==================================
        self.prefer_final = zc.buildout.easy_install.prefer_final()


        self.old_home = os.environ.get('HOME')
        os.environ['HOME'] = 'bbbBadHome'

        self.tmp = tempfile.mkdtemp('buildouttests')
        zc.buildout.easy_install.default_index_url = 'file://'+self.tmp
        os.environ['buildout-testing-index-url'] = (
            zc.buildout.easy_install.default_index_url)

        sample = os.path.join(self.tmp, 'sample-buildout')
        self.buildout_dir = sample
        os.mkdir(sample)

        self.old_dir = os.getcwd()
        os.chdir(sample)

        # Create a basic buildout.cfg to avoid a warning from buildout:
        open('buildout.cfg', 'w').write(
            "[buildout]\nparts =\n"
            )

        # Use the buildout bootstrap command to create a buildout
        Buildout(
            'buildout.cfg',
            [('buildout', 'log-level', 'WARNING'),
             # trick bootstrap into putting the buildout develop egg
             # in the eggs dir.
             ('buildout', 'develop-eggs-directory', 'eggs'),
             ]
            ).bootstrap([])

    
        # Create the develop-eggs dir, which didn't get created the usual
        # way due to thr trick above:
        os.mkdir('develop-eggs')
        self.buildout_cmd = os.path.join(sample, 'bin', 'buildout')

        zc.buildout.easy_install.prefer_final(self.prefer_final)

        # Setup the recipes
        destination = os.path.join(sample, 'develop-eggs')
        for package in ['djangorecipe']:
            dist = pkg_resources.working_set.find(
                pkg_resources.Requirement.parse('djangorecipe'))
            open(os.path.join(destination, 'djangorecipe.egg-link'), 'w'
                 ).write(dist.location)

        for package in ['zc.recipe.egg']:
            dist = pkg_resources.working_set.find(
                pkg_resources.Requirement.parse(package))

            target = os.path.join(destination,
                                  os.path.basename(dist.location),
                                  )
            if os.path.isdir(dist.location):
                shutil.copytree(dist.location, target)
            else:
                shutil.copyfile(dist.location, target)


    def tearDown(self):
        os.chdir(self.old_dir)
        os.environ['HOME'] = self.old_home
        shutil.rmtree(self.tmp)

    def buildout(self, env=None):
        command = subprocess.Popen(self.buildout_cmd,
                                   shell=True,
                                   env=env,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        command.wait()
        # Check for errors
        output = command.stdout.read()
        output += command.stderr.read()
        if 'Error:' in output:
            raise IOError('Problem during buildout run, output:\n\n' + output)

#     def testTrunk(self):
#         # Test a download from the Subversion repository
#         open('buildout.cfg', 'w').write('''
# [buildout]
# parts = django

# [django]
# recipe = djangorecipe
# version = trunk
# settings = development
# project = dummyshop
# ''')
#         self.buildout()

#     def testRelease(self):
#         # Test a release download
#         open('buildout.cfg', 'w').write('''
# [buildout]
# parts = django

# [django]
# recipe = djangorecipe
# version = 0.96.1
# settings = development
# project = dummyshop
# ''')
#         self.buildout()
#         self.failUnlessManage('django')

    def testDownloadDir(self):
        # Test a release download
        os.environ['HOME'] = self.old_home
        open('buildout.cfg', 'w').write('''
[buildout]
parts = django

[django]
recipe = djangorecipe
version = 0.96.1
settings = development
project = dummyshop
''')
        self.buildout(env=os.environ)
        self.failUnlessManage('django', '0.96.1')


    def failUnlessManage(self, script_name, version):
        script = os.path.join(self.buildout_dir, 'bin', script_name)
        # Make sure it exists
        self.failUnless(os.path.exists(script))
        command = subprocess.Popen([script, '--version'], 
                                   stdout=subprocess.PIPE)
        command.wait()
        # Check output of the Django script
        self.failUnlessEqual(command.stdout.read().strip(), version)
        


def test_suite():
    return unittest.makeSuite(TestRecipe)
