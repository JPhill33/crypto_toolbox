# -*- coding: utf-8 -*-
"""
Created on Sat Jul  2 14:19:28 2022

@author: joshphillips
"""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='crypto_toolbox',
    version='0.0.1',
    author='Josh Phillips',
    author_email='joshuataylorphillips@gmail.com',
    description='Package for crypto metrics and borrowing/lending analysis',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/JPhill33/crypto_toolbox.git',
    license='MIT',
    packages=['crypto_toolbox'],
    install_requires=['requests', 'json', 'urllib.request', 'pandas', 'statistics', 'numpy', 'datetime'],
)

