import os

from setuptools import setup, find_packages

version = '0.22'

def read_file(name):
    return open(os.path.join(os.path.dirname(__file__),
                             name)).read()

readme = read_file('README.txt')
changes = read_file('CHANGES.txt')

setup(name='djangorecipe',
      version=version,
      description="Buildout recipe for Django",
      long_description='\n\n'.join([readme, changes]),
      classifiers=[
        'Framework :: Buildout',
        'Framework :: Django',
        'Topic :: Software Development :: Build Tools',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        ],
      package_dir={'': 'src'},
      packages=find_packages('src'),
      keywords='',
      author='Roland van Laar',
      author_email='roland@micite.net',
      url='https://launchpad.net/djangorecipe',
      license='BSD',
      zip_safe=False,
      install_requires=[
        'zc.buildout',
        'zc.recipe.egg',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [zc.buildout]
      default = djangorecipe.recipe:Recipe
      """,
      )
