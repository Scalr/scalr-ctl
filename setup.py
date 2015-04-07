from setuptools import setup


setup(
    name='scalr-tools',
    version='2.0',
    py_modules=[
        'scalrtools.app',
        'scalrtools.view',
        'scalrtools.settings',
        'scalrtools.request',
    ],
    include_package_data=True,
    install_requires=[
        'Click',
        'prettytable',
        'pyyaml'
    ],
    entry_points='''
        [console_scripts]
        scalr-tools=scalrtools.app:cli
    ''',
)


# pip install PyYAML --global-option='--without-libyaml'