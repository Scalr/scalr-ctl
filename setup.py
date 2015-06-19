from setuptools import setup


setup(
    name='scalr-tools',
    version='2.0',
    packages = [
        "scalrtools",
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