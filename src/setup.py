from setuptools import setup

setup(
    name='scalr-tools',
    version='2.0',
    py_modules=['app'],
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        scalr-tools=app:cli
    ''',
)
