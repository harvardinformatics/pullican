'''
Created on Oct 31, 2016

@author: Aaron Kitzmiller <aaron_kitzmiller@harvard.edu>
@copyright: 2016 The Presidents and Fellows of Harvard College. All rights reserved.
@license: GPL v2.0
'''
import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pullican",
    version = "0.0.1",
    author = "Aaron Kitzmiller",
    author_email = "aaron_kitzmiller@harvard.edu",
    description = ("Simple WSGI application for rebuilding a Pelican website based on a github repository hook."),
    license = "GPL v2.0",
    keywords = "Pelican wsgi",
    url = "https://github.com/harvardinformatics/pullican",
    packages=['pullican'],
    long_description=read('README.txt'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
    ],
)