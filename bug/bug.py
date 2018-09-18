class Bug(object):
    def __init__(self, issue, commit, test, desc):
        self.issue = issue
        self.commit = commit
        self.test = test
        self.desc = desc
    def __str__(self):
        return 'description: '+self.desc+'\n'+'issue: '+self.issue.key+'\n'+'commit: '+self.commit.hexsha+'\n'+'test: '+self.test.get_mvn_name()

class BugError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

created_msg = 'Created in commit'
regression_msg = 'Regression test bug'
invalid_msg = 'Invalid: testcase generated compilation error when patched'