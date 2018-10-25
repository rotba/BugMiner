from setuptools import setup, find_packages

install_requires = ['GitPython', 'javalang', 'distance', 'jira', 'mvnpy', 'sfl_diagnoser']

setup(
    name='BugMiner',
    version='1.0.1',
    packages=find_packages(),
    url='https://github.com/rotba/BugMiner',
    license='',
    author='Rotem Barak',
    author_email='rotba@post.bgu.ac.il',
    install_requires=install_requires,
    description='Python Distribution Utilities'
)
