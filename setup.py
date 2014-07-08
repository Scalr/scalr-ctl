'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''
import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

description = "Scalr-tools is a command-line interface to your Scalr account"

cfg = dict(
	name = "scalr",
	version = read("VERSION"),
	description = description,
	author = "Scalr Inc.",
	author_email = "dmitry@scalr.com",
	url = "https://scalr.net",
	license = "GPL",
	platforms = "any",
	packages = find_packages(),
	include_package_data = True,
	scripts=['bin/scalr'],
	install_requires = ["prettytable"],
	long_description=read('README'),
	classifiers=[
		'Programming Language :: Python',
		'Programming Language :: Python :: 2',
		'License :: OSI Approved :: GNU General Public License (GPL)',
		'Operating System :: OS Independent',
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: System Administrators',
		'Topic :: Utilities'
		]
	)
setup(**cfg)
