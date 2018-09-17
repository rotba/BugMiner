import os
import unittest
import Main
import bug.bug as my_bug
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
        self.issue_19 = Main.jira.issue('TIKA-19')
        commit = [c for c in Main.all_commits if c.hexsha == '52e80f56a2f2877ff2261889b1dc180c51b72f6b'][0]
        tests = Main.get_tests_from_commit(commit)
        res = Main.extract_bugs(self.issue_19, commit, tests)
        for bug in res:
            if bug.commit.hexsha =='52e80f56a2f2877ff2261889b1dc180c51b72f6b' and 'NaimTest#newGooTest' in bug.test.get_name() and bug.msg =='Created in test':
                return
        self.fail('Did not extracted bug : created test - \'NaimTest#newGooTest\'')

    def test_find_test_cases_diff(self):
        print('test_find_test_cases_diff')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        commit = [c for c in Main.all_commits if c.hexsha == '14ef5aa7f71f2beb78f38227399ec4b3388b4127'][0]
        test_report_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_2\target\surefire-reports\TEST-p_1.AssafTest.xml'
        module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_2'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system('mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f '+module_path)
        test = Main.test_parser.TestClass(test_report_path, module_path)
        expected_delta_testcase = [t for t in test.testcases if 'p_1.AssafTest#goo' in t.get_name()][0]
        Main.prepare_project_repo_for_testing(commit.parents[0], module_path)
        diff_testcases =Main.find_test_cases_diff(test, test.src_path)
        self.assertTrue(expected_delta_testcase in diff_testcases)

    def test_get_commit_created_testclasses(self):
        print('test_get_commit_created_testclasses')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        commit = [c for c in Main.all_commits if c.hexsha == 'e00037324027af30134ee1554b93f5969f8f100e'][0]
        test_report_path = os.getcwd()+'r\tested_project\GitMavenTrackingProject\sub_mod_1\target\surefire-reports\TEST-p_1.AmitTest.xml'
        module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        commit_tests = Main.test_parser.get_tests(module_path)
        expected_delta_testclass = [t for t in commit_tests if 'p_1.AmitTest' in t.get_name()][0]
        Main.prepare_project_repo_for_testing(commit.parents[0], module_path)
        diff_testclasses = Main.get_commit_created_testclasses(commit_tests)
        self.assertTrue(expected_delta_testclass in diff_testclasses)

    def test_patch_tescases(self):
        print('test_patch_tescases')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        commit = [c for c in Main.all_commits if c.hexsha == 'e00037324027af30134ee1554b93f5969f8f100e'][0]
        parent = commit.parents[0]
        test_report_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_1\target\surefire-reports\TEST-p_1.AmitTest.xml'
        module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        commit_tests = Main.test_parser.get_tests(module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_delta_testcase = [t for t in commit_testcases if 'p_1.AmitTest#hoo' in t.get_name()][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        patched_tests = Main.patch_testcases(commit_testcases, commit, parent)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        parent_tests = Main.test_parser.get_tests(module_path)
        parent_testcases=Main.test_parser.get_testcases(parent_tests)
        self.assertTrue(expected_delta_testcase in parent_testcases, "'p_1.AmitTest should have been patchd on the parent commit and exist")


    def test_patch_tescases_not_compiling_testcases(self):
        print('test_patch_tescases_not_compiling_testcases')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        commit = [c for c in Main.all_commits if c.hexsha == 'a71cdc161b0d87e7ee808f5078ed5fefab758773'][0]
        parent = commit.parents[0]
        test_report_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_1\target\surefire-reports\TEST-p_1.AmitTest.xml'
        module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        commit_tests = Main.test_parser.get_tests(module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_not_compiling_testcase = [t for t in commit_testcases if 'MainTest#gooTest' in t.get_name()][0]
        commit_new_testcases = Main.get_commit_created_testcases(commit_testcases)
        Main.prepare_project_repo_for_testing(parent, module_path)
        patched_testcases = Main.patch_testcases(commit_testcases, commit, parent)
        not_compiling_testcases = [t for t in commit_new_testcases if not t in patched_testcases]
        self.assertTrue(not expected_not_compiling_testcase in not_compiling_testcases, "'p_1.MainTest#gooTest should have been picked as for compilation error")
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        parent_tests = Main.test_parser.get_tests(module_path)
        parent_testcases = Main.test_parser.get_testcases(parent_tests)
        self.assertTrue(len(parent_testcases)>0,
                        'Build probably failed')
        self.assertTrue(not expected_not_compiling_testcase in parent_testcases, expected_not_compiling_testcase.get_name()+' shoukd have been unpatched')


    def test_get_compilation_error_testcases(self):
        print('test_get_compilation_error_testcases')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        with open(os.getcwd()+r'\static_files\test_get_compilation_error_testcases_report.txt','r') as report_file:
            report = report_file.read()
        commit = [c for c in Main.all_commits if c.hexsha == 'a71cdc161b0d87e7ee808f5078ed5fefab758773'][0]
        parent = commit.parents[0]
        cached_module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject_installed\sub_mod_1'
        module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        commit_tests = Main.test_parser.get_cached_tests(cached_module_path, module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_not_compiling_testcase = [t for t in commit_testcases if 'MainTest#gooTest' in t.get_name()][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        commit_new_testcases = Main.get_commit_created_testcases(commit_testcases)
        compolation_error_testcases = Main.get_compilation_error_testcases(report, commit_new_testcases)
        self.assertTrue(expected_not_compiling_testcase in compolation_error_testcases,
                        "'MainTest#gooTest should have been picked as for compilation error")


    def test_extract_bugs(self):
        print('test_extract_bugs')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        exp_test_src_patch = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_1\src\test\java\MainTest.java'
        commit = [c for c in Main.all_commits if c.hexsha == '1fd244f006c96fa820efa850f5f31e3f9a727d84'][0]
        cached_module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject_installed'
        module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject'
        tests = Main.test_parser.get_cached_tests(cached_module_path,module_path)
        commit_tests = list(filter(lambda t: 'NaimTest' in t.get_name() or 'MainTest' in t.get_name(), tests))
        res = Main.extract_bugs(None, commit, commit_tests)
        for bug in res:
            if bug.test.get_src_path() == exp_test_src_patch and bug.desc == my_bug.created_msg:
                return
        self.fail('Did not extracted the bug from the file -'+ exp_test_src_patch)

    def test_get_commit_created_testcases(self):
        print('test_get_commit_created_testcases')
        Main.set_up('https://github.com/rotba/GitMavenTrackingProject')
        exp_test_src_patch = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_1\src\test\java\MainTest.java'
        commit = [c for c in Main.all_commits if c.hexsha == '1fd244f006c96fa820efa850f5f31e3f9a727d84'][0]
        parent = commit.parents[0]
        cached_module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject_installed'
        module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject'
        tests = Main.test_parser.get_cached_tests(cached_module_path, module_path)
        testcases = Main.test_parser.get_testcases(tests)
        Main.prepare_project_repo_for_testing(parent, module_path)
        new_testcases = Main.get_commit_created_testcases(testcases)
        expected_new_testcase = [t for t in testcases if 'MainTest#foo_2' in t.get_name()][0]
        self.assertTrue(expected_new_testcase in new_testcases, 'MainTest#foo_2 should be picked for being new test')


if __name__ == '__main__':
    unittest.main()