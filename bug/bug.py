import copy
import csv


class Bug(object):
    def __init__(self, issue, commit, test, desc):
        self._issue = issue
        self._commit = commit
        self._test = test
        self._desc = desc

    @property
    def issue(self):
        return self._issue
    @property
    def commit(self):
        return self._commit
    @property
    def test(self):
        return copy.deepcopy(self._test)
    @property
    def desctiption(self):
        return copy.deepcopy(self._desc)
    def __str__(self):
        return 'description: '+self._desc+'\n'+'issue: '+self.issue.key+'\n'+'commit: '+self._commit.hexsha+'\n'+'test: '+self._test.get_id()

class Bug_csv_report_handler(object):
    def __init__(self, path):
        self._writer = None
        self._path = path
        self._fieldnames = ['issue', 'commit', 'testcase', 'description']
        with open(self._path, 'w+', newline='') as csv_output:
            writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames)
            writer.writeheader()
     #Adds bug to the csv file
    def add_bug(self, bug):
        with open(self._path, 'a', newline='') as csv_output:
            writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames)
            writer.writerow(self.generate_csv_tupple(bug))

    # Adds bugs to the csv file
    def add_bugs(self, bugs):
        with open(self._path, 'a', newline='') as csv_output:
            writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames)
            for bug in bugs:
                writer.writerow(self.generate_csv_tupple(bug))

    # Generated csv bug tupple
    def generate_csv_tupple(self, bug):
        return {'issue': bug.issue.key,
                'commit': bug.commit.hexsha,
                'testcase': bug.test.get_id(),
                'description': bug.desctiption}

class BugError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


created_msg = 'Created in commit'
regression_msg = 'Regression test bug'
invalid_msg = 'Invalid: testcase generated compilation error when patched'

