'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

from setuptools import setup, find_packages


description = "Pecha is a command-line interface to your Scalr account"


cfg = dict(
	name = "pecha",
	version = "0.3.2",	 
	description = description,
	long_description = description,
	author = "Scalr Inc.",
	author_email = "info@scalr.net",
	url = "https://scalr.net",
	license = "GPL",
	platforms = "any",
	packages = find_packages(),
	scripts=['bin/pecha'],
	install_requires = ["prettytable"],
)
setup(**cfg)


