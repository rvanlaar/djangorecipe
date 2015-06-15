import os

from setuptools import setup, find_packages

version = '2.1'


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__),
                             name)).read()

readme = read_file('README.rst')
changes = read_file('CHANGES.rst')

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
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        ],
      package_dir={'': 'src'},
      packages=find_packages('src'),
      keywords='',
      author='Roland van Laar',
      author_email='roland@micite.net',
      url='https://github.com/rvanlaar/djangorecipe',
      license='BSD',
      zip_safe=False,
      install_requires=[
        'zc.buildout',
        'zc.recipe.egg',
        'Django',
      ],
      extras_require={'test': ['coverage',
                               'mock']},
      entry_points="""
      # -*- Entry points: -*-
      [zc.buildout]
      default = djangorecipe.recipe:Recipe
      """,
      )
