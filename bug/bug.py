class Bug(object):
    def __init__(self, issue, commit, tests, desc):
        self.issue = issue
        self.commit = commit
        self.tests = tests
        self.desc = desc
    def __str__(self):
        str =  'description: '+self.desc+'\n'+'issue: '+self.issue.key+'\n'+'commit: '+self.commit.hexsha+'\n'
        'tests: '
        for test in self.tests:
            str+='\n\t'+test.get_name()
        return str

class BugError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.value)