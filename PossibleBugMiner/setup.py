from setuptools import setup, find_packages

from settings import CURRENT_PROJ_NAME

install_requires = ['GitPython','jira', 'AIDnD_Diff']



setup(
    name=CURRENT_PROJ_NAME,
    version='1.0.0',
    packages=find_packages(),
    url='https://github.com/rotba/{}'.format(CURRENT_PROJ_NAME),
    license='',
    author='Rotem Barak',
    author_email='rotemb271@gmail.com',
    install_requires=install_requires,
    description='Python Distribution Utilities'
)
