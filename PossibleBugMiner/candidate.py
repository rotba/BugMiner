import logging
import settings
from mvnpy import mvn
from pathlib import Path
import os


class Candidate(object):
    TESTS_DIFFS_IS_CRITERIA = False

    def __init__(self, issue, fix_commit, tests, diffed_components):
        self._issue = issue
        self._fix_commit = fix_commit
        self._tests = tests
        self._diffed_components = diffed_components

    @property
    def issue(self):
        return self._issue

    @property
    def fix_commit(self):
        return self._fix_commit

    @property
    def tests(self):
        return self._tests

    @property
    def diffed_components(self):
        return self._diffed_components
