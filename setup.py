import os

from setuptools import setup, find_packages

version = '0.8'

readme = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           'README.txt')).read()

setup(name='djangorecipe',
      version=version,
      description="Buildout recipe for Django",
      long_description=readme,
      classifiers=[
        'Framework :: Buildout',
        'Framework :: Django',
        'Topic :: Software Development :: Build Tools',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        ], 
      package_dir={'': 'src'},
      packages=find_packages('src'),
      keywords='',
      author='Jeroen Vloothuis',
      author_email='jeroen.vloothuis@xs4all.nl',
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
      default = djangorecipe:Recipe
      """,
      )
