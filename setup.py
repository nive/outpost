import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'waitress',
    'requests'
    ]

setup(name='outpost',
      version='0.1',
      description='Anti cors html application/webservice development server',
      long_description='',
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Arndt Droullier, Nive GmbH',
      author_email='info@nive.co',
      url='http://cms.nive.co',
      keywords='fileserver proxy development cors web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="outpost",
      entry_points = """\
        [pyramid.scaffold]
        default=outpost.scaffolds:DefaultTemplate
      """
      )

