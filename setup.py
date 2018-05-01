#! /usr/bin/env python3

import io
from setuptools import setup, find_packages
import re

version = ''
with io.open('tgminer/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

readme = ''
with io.open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(name='tgminer',
      python_requires='>=3.5',
      author='Teriks',
      author_email='Teriks@users.noreply.github.com',
      url='https://github.com/Teriks/TGMiner',
      version=version,
      packages=find_packages(),
      license='BSD 3-Clause',
      description='Telegram data mining client',
      long_description=readme,
      include_package_data=True,
      install_requires=["python-slugify",
                        "whoosh~=2.7",
                        "tgcrypto~=1.0",
                        "jsoncomment~=0.3",
                        "fasteners~=0.14",
                        "dschema~=0.3a1",
                        'kovit~=0.1a1',
                        'pyrogram==1000.0'],
      dependency_links=['https://github.com/Teriks/pyrogram/archive/master.zip#egg=pyrogram-1000.0'],
      entry_points={
          'console_scripts': [
              'tgminer = tgminer.tgminer:main',
              'tgminer-search = tgminer.search:main',
              'tgminer-markov = tgminer.markov:main'
          ]
      },
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: BSD License',
          'Intended Audience :: Other Audience',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Topic :: Utilities',
      ]
      )
