class Bug:
    def __init__(self, issue, commit, test, diffs):
        self.issue = issue
        self.commit = commit
        self.test = test

class BugError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.value)