from distutils.core import setup
from distutils.command.install_data import install_data

try:
    from post_setup import main as post_install
except ImportError:
    post_install = lambda: None

class my_install(install_data):
    def run(self):
        install_data.run(self)
        post_install()

if __name__ == '__main__':

    setup(
        cmdclass={'install': my_install},
        name='scalr-tools',
        version='1.0',
        packages = [
            "scalrtools",
            "scalrtools.commands",
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
            scalr-tools=scalrtools.app:cli
        ''',
    )


# pip install PyYAML --global-option='--without-libyaml'