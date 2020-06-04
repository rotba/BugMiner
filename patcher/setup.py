from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = ['javalang', 'GitPython','AIDnD_mvnpy']

setup(
    name='patcher',
    version='1.0.1',
    packages=find_packages(),
    url='https://github.com/rotba/patcher',
    license='',
    author='Rotem Barak',
    author_email='rotemb271@gmail.com',
    install_requires=install_requires,
    long_description=long_description,
    long_description_content_type="text/markdown",
	classifiers=[
        "Programming Language :: Python :: 2.7 anconda",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)


