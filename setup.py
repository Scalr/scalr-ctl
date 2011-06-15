'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

from setuptools import setup, find_packages


description = "Scalr is a command-line interface to your Scalr account"


cfg = dict(
	name = "scalr",
	version = "0.3.14",	 
	description = description,
	long_description = description,
	author = "Scalr Inc.",
	author_email = "dmitry@scalr.com",
	url = "https://scalr.net",
	license = "GPL",
	platforms = "any",
	packages = find_packages(),
	scripts=['bin/scalr'],
	install_requires = ["prettytable"],
)
setup(**cfg)

