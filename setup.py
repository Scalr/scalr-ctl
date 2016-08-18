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
        post_install()  # Does not work with pip


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

description = "Scalr-ctl is a command-line interface to your Scalr account"


if __name__ == '__main__':

    setup(
        name='scalr-ctl',
        version=read("scalrctl/VERSION").strip(),
        description=description,
        author="Scalr Inc.",
        author_email="dmitry@scalr.com",
        url="https://scalr.net",
        license="Apache-2",
        platforms="any",
        long_description=read('README'),
        classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: System Administrators',
            'Topic :: Utilities'
            ],
        packages=[
            "scalrctl",
            "scalrctl.click",
            "scalrctl.commands",
            "scalrctl.commands.internal"
        ],
        include_package_data=True,
        package_data={
            '': ['VERSION', 'scheme/scheme.json'],
        },
        data_files=[('', ['scalrctl/scheme/scheme.json', ]), ],
        install_requires=[
            'prettytable>=0.7.2',
            'pyyaml>=3.11',
            'requests>=2.10.0',
            'six>=1.10.0',
            'colorama>=0.3.7',
            'dicttoxml>=1.7.4',
        ],
        entry_points='''
            [console_scripts]
            scalr-ctl=scalrctl.app:cli
        ''',
    )
