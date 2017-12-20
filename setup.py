#!/usr/bin/env python

from setuptools import setup

setup(
    name='neofetch',
    version='1.0',
    description='Python neofetch',
    author='Siddharth Dushantha',
    author_email='siddharth.dushantha@gmail.com',
    url='https://github.com/sdushantha/neofetch',
    packages=['neofetch'],
    entry_points = {
        'console_scripts': ['neofetch=neofetch.neofetch:main'],
    }
)
