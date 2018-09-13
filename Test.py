import sys
import unittest
import Main

class TestMain(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skip("Long test")
    def test_issue_1378_get_issue_tests(self):
        Main.set_up('https://github.com/apache/tika')
        self.issue_1378 = Main.jira.issue('TIKA-1378')
        self.issue_19 = Main.jira.issue('TIKA-19')
        try:
            tests = Main.get_issue_tests(self.issue_1378)
        except Main.bug.BugError as e:
            self.fail('get_issue_tests() did not associate TIKA-1378 with HtmlEncodingDetectorTest')
        for test in tests:
            if 'MicrosoftTranslatorTest' in test.get_name():
                return
        self.fail('get_issue_tests() did not associate TIKA-1378 with HtmlEncodingDetectorTest' )

    @unittest.skip("Long test")
    def test_issue_1378_get_issue_commits(self):
        Main.set_up('https://github.com/apache/tika')
        self.issue_1378 = Main.jira.issue('TIKA-1378')
        self.issue_19 = Main.jira.issue('TIKA-19')
        try:
            commits = Main.get_issue_commits(self.issue_1378)
        except Main.bug.BugError as e:
            self.fail('get_issue_commits() did not associate TIKA-1378 with commit 65aea2b06b33c6b53999b6c52e017c38bf2af0b4')
        for commit in commits:
            if commit.hexsha=='65aea2b06b33c6b53999b6c52e017c38bf2af0b4':
                return
        self.fail('get_issue_commits() did not associate TIKA-1378 with commit 65aea2b06b33c6b53999b6c52e017c38bf2af0b4' )

    @unittest.skip("Long test")
    def test_issue_1378_get_tests_from_commit(self):
        Main.set_up('https://github.com/apache/tika')
        self.issue_1378 = Main.jira.issue('TIKA-1378')
        commit = Main.repo.commit('65aea2b06b33c6b53999b6c52e017c38bf2af0b4')
        res_tests = Main.get_tests_from_commit(commit)
        for test in res_tests:
            if commit.get_name() == '65aea2b06b33c6b53999b6c52e017c38bf2af0b4':
                return
        self.fail(
            'get_issue_commits() did not associate TIKA-1378 with commit 65aea2b06b33c6b53999b6c52e017c38bf2af0b4')

    @unittest.skip("Master test")
    def test_issue_1378_get_fixes(self):
        Main.set_up('https://github.com/apache/tika')
        self.issue_1378 = Main.jira.issue('TIKA-1378')
        self.issue_19 = Main.jira.issue('TIKA-19')
        commits = Main.get_issue_commits(self.issue_1378)
        tests = Main.get_issue_tests(self.issue_1378)
        fixes = Main.get_fixes(commits, tests)
        for fix in fixes:
            if fix[0]=='65aea2b06b33c6b53999b6c52e017c38bf2af0b4' and fix[1]=='MicrosoftTranslatorTest':
                return
        self.fail('get_fixes() did not associate commit 65aea2b06b33c6b53999b6c52e017c38bf2af0b4 with MicrosoftTranslatorTest' )

    @unittest.skip("Master test")
    def test_a_issue_19_get_issue_tests(self):
        Main.set_up('https://github.com/apache/tika')
        self.issue_19 = Main.jira.issue('TIKA-19')
        print('test_a_issue_19_get_issue_tests')
        issue = self.issue_19
        try:
            tests = Main.get_issue_tests(issue)
        except Main.bug.BugError as e:
            self.fail('get_issue_tests() did not associate TIKA-19 with TestParsers')
        for test in tests:
            if 'TestParsers' in test.get_name():
                return
        self.fail('get_issue_tests() did not associate TIKA-19 with TestParsers' )

    @unittest.skip("Master test")
    def test_b_issue_19_get_issue_commits(self):
        Main.set_up('https://github.com/apache/tika')
        self.issue_1378 = Main.jira.issue('TIKA-1378')
        self.issue_19 = Main.jira.issue('TIKA-19')
        print('test_b_issue_19_get_issue_commits')
        issue = self.issue_19
        try:
            commits = Main.get_issue_commits(issue)
        except Main.bug.BugError as e:
            self.fail('get_issue_commits() did not associate TIKA-19 with commit d7dabee5ce14240f3c5ba2f6147c963d03604dd3')
        for commit in commits:
            if commit.hexsha=='d7dabee5ce14240f3c5ba2f6147c963d03604dd3':
                return
        self.fail('get_issue_commits() did not associate TIKA-19 with commit d7dabee5ce14240f3c5ba2f6147c963d03604dd3' )

    @unittest.skip("Master test")
    def test_c_issue_19_exrtact_bugs(self):
        Main.set_up('https://github.com/apache/tika')
        self.issue_19 = Main.jira.issue('TIKA-19')
        print('test_c_issue_19_get_fixes')
        issue = self.issue_19
        commits = Main.get_issue_commits(issue)
        tests = Main.get_issue_tests(issue)
        bugs = Main.extract_bugs(issue, commits[0], tests)
        for bug in bugs:
            if bug.commit.hexsha=='d7dabee5ce14240f3c5ba2f6147c963d03604dd3' and 'TestParsers' in bug.test.get_name():
                return
        self.fail('get_fixes() did not associate commit d7dabee5ce14240f3c5ba2f6147c963d03604dd3 with TestParsers' )

    @unittest.skip("Master test")
    def test_issue_19_is_associated_to_commit(self):
        Main.set_up('https://github.com/apache/tika')
        self.issue_19 = Main.jira.issue('TIKA-19')
        print('test_issue_19_is_associated_to_commit')
        issue = self.issue_19
        associated_commits = []
        all_commits = Main.all_commits
        for commit in all_commits:
            if Main.is_associated_to_commit(issue, commit):
                associated_commits.append(commit)
        self.assertTrue(len(associated_commits)==1,
                        'Excpected associated commits: 1 and got: '+str(len(associated_commits)))
        self.assertEqual(associated_commits[0].hexsha, 'd7dabee5ce14240f3c5ba2f6147c963d03604dd3',
                         'Excpected associated commit: d7dabee5ce14240f3c5ba2f6147c963d03604dd3 \n'+
                         'But got: ' + associated_commits[0].hexsha)


    @unittest.skip("Not relevant")
    def test_issue_get_diffs(self):
        print('test_issue_get_diffs')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        commit_test_pass_hash = '1df5710687471a8b47dca2d6f39659efab9c1063'
        all_commits = Main.all_commits
        all_tests = Main.all_tests
        commit = [c for c in all_commits if c.hexsha==commit_test_pass_hash][0]
        test = [t for t in all_tests if t.get_name() == 'NaimTest'][0]
        diffs = Main.get_diffs(commit, test)
        x=1


    def test_get_tests_from_commit(self):
        print('test_get_tests_from_commit')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        commit = [c for c in Main.all_commits if c.hexsha == '52e80f56a2f2877ff2261889b1dc180c51b72f6b'][0]
        tests = Main.get_tests_from_commit(commit)
        self.assertEqual(len(tests), 1,
                         'Only one test should be associated with 52e80f56a2f2877ff2261889b1dc180c51b72f6b')
        self.assertTrue('NaimTest' in tests[0].get_name(),
                         '\'NaimTest\' should be associated with 52e80f56a2f2877ff2261889b1dc180c51b72f6b')

    def test_created_test_extract_bugs(self):
        print('test_created_test_extract_bugs')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        commit = [c for c in Main.all_commits if c.hexsha == '52e80f56a2f2877ff2261889b1dc180c51b72f6b'][0]
        tests = Main.get_tests_from_commit(commit)
        res = Main.extract_bugs(None, commit, tests)
        for bug in res:
            if bug.commit.hexsha =='52e80f56a2f2877ff2261889b1dc180c51b72f6b' and 'NaimTest#newGooTest' in bug.test.get_name() and bug.msg =='Created in test':
                return
        self.fail('Didn\'t extracted created test - \'NaimTest#newGooTest\'')


    def test_say_hello(self):
        self.assertEqual(Main.say_hello(), 'hello')


if __name__ == '__main__':
    unittest.main()