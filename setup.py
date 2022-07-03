# -*- coding: utf-8 -*-
"""
Created on Sat Jul  2 14:19:28 2022

@author: joshphillips
"""

import setuptools


setuptools.setup(
    name='crypto_toolbox',
    version='0.0.1',
    author='Josh Phillips',
    author_email='joshuataylorphillips@gmail.com',
    description='Package for crypto metrics and borrowing/lending analysis',
    url='https://github.com/JPhill33/crypto_toolbox',
    license='MIT',
    packages=['crypto_toolbox'],
    install_requires=['requests', 'json', 'urllib', 'pandas', 'statistics', 'numpy', 'datetime'],
)

