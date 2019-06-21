import os
from setuptools import setup, find_packages
from pylicenses import version

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='pylicenses',
    version=version,
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    description='License scanning and documentation for conda and pip envs',
    long_description=README,
    url='https://github.com/miraculixx/pylicenses',
    author='Patrick Senti',
    author_email='patrick.senti@productaize.io',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    install_requires=[
        'sh==1.12.14',
        'requests==2.21.0',
        'tabulate==0.8.2',
    ],
)
