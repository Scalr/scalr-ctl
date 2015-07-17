import os

from distutils.core import setup
from distutils.command.install import install


try:
    from post_setup import main as post_install
except ImportError:
    post_install = lambda: None


class _install(install):
    def run(self):
        install.run(self)
        post_install()

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

description = "Scalr-ctl is a command-line interface to your Scalr account"


if __name__ == '__main__':

    setup(
        name='scalr-ctl',
        version = read("VERSION").strip(),
        description = description,
        author = "Scalr Inc.",
        author_email = "dmitry@scalr.com",
        url = "https://scalr.net",
        license = "GPL",
        platforms = "any",
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
            ],
        packages = [
            "scalrctl",
            "scalrctl.commands",
        ],
        include_package_data=True,
        install_requires=[
            'Click',
            'prettytable',
            'pyyaml',
            'requests'
        ],
        entry_points='''
            [console_scripts]
            scalr-ctl=scalrctl.app:cli
        ''',
    )