import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'waitress',
    'requests'
    ]

try:
    README = open(os.path.join(here, 'readme.rst')).read()
except:
    README = ''

setup(name='outpost',
      version='0.2.4',
      description='Local javascript application development server',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Testing",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "License :: OSI Approved :: BSD License"
        ],
      author='Arndt Droullier, Nive GmbH',
      author_email='info@nive.co',
      url='http://www.nive.co',
      keywords='server proxy development cors web pyramid',
      packages=find_packages(),
      include_package_data=True,
      license='BSD 3',
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="outpost",
      entry_points = """\
        [pyramid.scaffold]
        default=outpost.scaffolds:DefaultTemplate
      """
      )

