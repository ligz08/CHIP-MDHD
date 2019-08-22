from setuptools import setup, find_packages

setup(
    name='CHIP-MDHD',
    version='0.0.1',
    description='California Hydrogen Infrastructure Planning Model for Medium-Duty and Heavy-Duty Vehicles',
    long_description=open('README.md', 'r').read(),
    long_description_content_type="text/markdown",
    author='Guozhen Li',
    author_email='ligz@ucdavis.edu',
    packages=find_packages(),
    install_requires=['pandas', 'networkx', 'gurobipy'],
    license='MIT',
    url='https://github.com/ligz08/CHIP-MDHD'
)