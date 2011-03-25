'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

from setuptools import setup, findall, find_packages
from distutils.command.install_data import install_data
import platform


description = "Scalarizr converts any server to Scalr-manageable node"


data_files = []
data_files.append(["/usr/local/bin", ["bin/scalarizr", 'bin/szradm']])


cfg = dict(
	name = "scalarizr",
	version = "0.7.0",	 
	description = description,
	long_description = description,
	author = "Scalr Inc.",
	author_email = "info@scalr.net",
	url = "https://scalr.net",
	license = "GPL",
	platforms = "any",
	package_dir = {"" : "src"},
	packages = find_packages(".n"),
	requires = ["prettytable"],
)
setup(**cfg)


