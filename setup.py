from setuptools import setup, find_packages
import sys, os

version = '0.1'

long_description = ""

setup(name='dpo',
      version=version,
      description="Tools to manage PO files without canonical source strings",
      long_description=long_description,
      classifiers=[], 
      keywords='',
      author='Ethan Jucovy',
      author_email='ethan.jucovy@gmail.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "polib",
        ],
      entry_points="""
      [console_scripts]
      dpo = dpo.console:main
      """,
      )
