from setuptools import setup, find_packages

version = '0.7'

setup(name='djangorecipe',
      version=version,
      description="Buildout recipe for Django",
      long_description="""
This buildout recipe can be used to create a setup for Django. It will
automatically download Django and install it in the buildout's
sandbox. You can use either a release version of Django or a
subversion checkout (by using `trunk` instead of a version number.

You can see an example of how to use the recipe below::

  [buildout]
  parts = satchmo django
  eggs = ipython
  
  [satchmo]
  recipe = gocept.download
  url = http://www.satchmoproject.com/snapshots/satchmo-0.6.tar.gz
  md5sum = 659a4845c1c731be5cfe29bfcc5d14b1
  
  [django]
  recipe = djangorecipe
  version = 0.96.1
  settings = development
  eggs = ${buildout:eggs}
  pythonpath = 
  ${satchmo:location}
  project = dummyshop
""",
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
