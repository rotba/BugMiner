class Bug(object):
    def __init__(self, issue, commit, test, desc):
        self.issue = issue
        self.commit = commit
        self.test = test
        self.desc = desc
    def __str__(self):
        return 'description: '+self.desc+'\n'+'issue: '+self.issue.key+'\n'+'commit: '+self.commit.hexsha+'\n'+'test: '+self.test.get_name()

class BugError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.value)