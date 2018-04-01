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
      install_requires=["python-slugify", "whoosh", "tgcrypto", "jsoncomment", "fasteners", "pyrogram", "dschema",
                        'markovify'],
      entry_points={
          'console_scripts': [
              'tgminer = tgminer.tgminer:main',
              'tgminer-search = tgminer.tgminersearch:main',
              'tgminer-markov = tgminer.tgminermarkov:main'
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
