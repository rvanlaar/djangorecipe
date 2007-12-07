from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='djangorecipe',
      version=version,
      description="Buildout recipe for Django",
      long_description="""\
A buildout recipe which can be used to create Django installation""",
      classifiers=[], 
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'zc.buildout',
        'zc.recipe.egg',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [zc.buildout]
      default = djangorecipe:Recipe

      """,
      )
