from setuptools import setup, find_packages

install_requires = ['GitPython', 'javalang', 'distance', 'jira']

setup(
    name='BugMiner',
    version='1.0.0',
    packages=find_packages(),
    url='https://github.com/rotba/BugMiner',
    license='',
    author='Rotem Barak',
    author_email='rotba@post.bgu.ac.il',
    install_requires=install_requires,
    description='Python Distribution Utilities'
)