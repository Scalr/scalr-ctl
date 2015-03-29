from setuptools import setup


setup(
    name='scalr-tools',
    version='2.0',
    py_modules=['app', 'view'],
    include_package_data=True,
    install_requires=[
        'Click',
        'prettytable'
        'pyyaml'
    ],
    entry_points='''
        [console_scripts]
        scalr-tools=app:cli
    ''',
)


# pip install PyYAML --global-option='--without-libyaml'