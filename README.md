## BugMiner

BugMiner is a python program used to extract bugs from Java projects.


### REQUIREMENTS

* Git (1.7.x or newer)
* Python 2.7

### INSTALL

If you have downloaded the source code:

    python setup.py install


### RUNNING TESTS

To run the the tests, simply run:

    python Test.py


### API

Extracting bugs:

The project you want to extract bugs from must be a Java project written in Maven framework, and has a Jira repository for tracking it's issues.

Example on apache\tika project:

    python Main.py https:\github.com\apache\tika http:\issues.apache.org\jira\projects\TIKA

If one desires to extract bugs from a specific issue, one can run

    python Main.py https:\github.com\apache\tika http:\issues.apache.org\jira\projects\TIKA TIKA-56

