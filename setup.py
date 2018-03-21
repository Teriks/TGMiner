#! /usr/bin/env python3

from setuptools import setup, find_packages
import re

version = ''
with open('tgminer/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')


readme = ''
with open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()


setup(name='tgminer',
      author='Teriks',
      author_email='Teriks@users.noreply.github.com',
      url='https://github.com/Teriks/TGMiner',
      version=version,
      packages=find_packages(exclude=("debian_packaging",)),
      license='BSD 3-Clause',
      description='Telegram data mining client',
      long_description=readme,
      include_package_data=True,
      install_requires=["python-slugify", "whoosh", "tgcrypto", "jsoncomment", "fasteners"],
      entry_points={
          'console_scripts': [
              'tgminer = tgminer.tgminer:main',
              'tgminer-search = tgminer.tgminersearch:main'
          ]
      },
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: BSD License',
          'Intended Audience :: Other Audience',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Utilities',
      ]
      )