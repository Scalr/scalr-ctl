'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''
import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

description = "Scalr is a command-line interface to your Scalr account"

cfg = dict(
	name = "scalr",
	version = "0.3.30",
	description = description,
	author = "Scalr Inc.",
	author_email = "dmitry@scalr.com",
	url = "https://scalr.net",
	license = "GPL",
	platforms = "any",
	packages = find_packages(),
	scripts=['bin/scalr'],
	install_requires = ["prettytable"],
	long_description=read('README')
)
setup(**cfg)

