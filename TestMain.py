import filecmp
import os
import unittest
import Main
import shutil
import bug.bug as my_bug


class TestMain(unittest.TestCase):

    def setUp(self):
        Main.GENERATE_DATA=False
        Main.USE_CACHE = False

    def tearDown(self):
        pass


    def test_check_out_and_get_tests_from_commit(self):
        print('test_check_out_and_get_tests_from_commit')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        commit = [c for c in Main.all_commits if c.hexsha == '52e80f56a2f2877ff2261889b1dc180c51b72f6b'][0]
        tests_paths = Main.get_tests_paths_from_commit(commit)
        tests = list(map(lambda t_path: Main.test_parser.TestClass(t_path), tests_paths))
        self.assertEqual(len(tests), 1,
                         'Only one test should be associated with 52e80f56a2f2877ff2261889b1dc180c51b72f6b')
        self.assertTrue('NaimTest' in tests[0].mvn_name,
                        '\'NaimTest\' should be associated with 52e80f56a2f2877ff2261889b1dc180c51b72f6b')

    @unittest.skip("Null test")
    def test_created_test_extract_bugs(self):
        print('test_created_test_extract_bugs')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        self.issue_19 = Main.jira.issue('TIKA-19')
        commit = [c for c in Main.all_commits if c.hexsha == '52e80f56a2f2877ff2261889b1dc180c51b72f6b'][0]
        tests_paths = Main.get_tests_paths_from_commit(commit)
        res = Main.extract_bugs(self.issue_19, commit, tests_paths)
        for bug in res:
            if bug.commit.hexsha == '52e80f56a2f2877ff2261889b1dc180c51b72f6b' and 'NaimTest#newGooTest' in bug.bugged_testcase.mvn_name and bug.msg == 'Created in test':
                return
        self.fail('Did not extracted bug : created test - \'NaimTest#newGooTest\'')

    def test_find_test_cases_diff(self):
        print('test_find_test_cases_diff')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        commit = [c for c in Main.all_commits if c.hexsha == '14ef5aa7f71f2beb78f38227399ec4b3388b4127'][0]
        test_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_2\src\test\java\p_1\AssafTest.java'
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_2'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        test = Main.test_parser.TestClass(test_path)
        expected_delta_testcase = [t for t in test.testcases if 'p_1.AssafTest#goo' in t.mvn_name][0]
        Main.prepare_project_repo_for_testing(commit.parents[0], module_path)
        diff_testcases = Main.find_test_cases_diff(test, test.src_path)
        self.assertTrue(expected_delta_testcase in diff_testcases)

    @unittest.skip("commit_created_testclasses() was deleted")
    def test_get_commit_created_testclasses(self):
        print('test_get_commit_created_testclasses')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        commit = [c for c in Main.all_commits if c.hexsha == 'e00037324027af30134ee1554b93f5969f8f100e'][0]
        test_report_path = os.getcwd() + 'r\tested_project\GitMavenTrackingProject\sub_mod_1\target\surefire-reports\TEST-p_1.AmitTest.xml'
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        commit_tests = Main.test_parser.get_tests(module_path)
        expected_delta_testclass = [t for t in commit_tests if 'p_1.AmitTest' in t.mvn_name][0]
        Main.prepare_project_repo_for_testing(commit.parents[0], module_path)
        diff_testclasses = Main.get_commit_created_testclasses(commit_tests)
        self.assertTrue(expected_delta_testclass in diff_testclasses)

    def test_patch_tescases(self):
        print('test_patch_tescases')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        commit = [c for c in Main.all_commits if c.hexsha == 'e00037324027af30134ee1554b93f5969f8f100e'][0]
        parent = commit.parents[0]
        test_report_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1\target\surefire-reports\TEST-p_1.AmitTest.xml'
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        commit_tests = Main.test_parser.get_tests(module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_delta_testcase = [t for t in commit_testcases if 'p_1.AmitTest#hoo' in t.mvn_name][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        patched_tests = Main.patch_testcases(commit_testcases, commit, parent, module_path)[0]
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        parent_tests = Main.test_parser.get_tests(module_path)
        parent_testcases = Main.test_parser.get_testcases(parent_tests)
        self.assertTrue(expected_delta_testcase in parent_testcases,
                        "'p_1.AmitTest should have been patchd on the parent commit and exist")

    def test_patch_tescases_not_compiling_testcases(self):
        print('test_patch_tescases_not_compiling_testcases')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        commit = [c for c in Main.all_commits if c.hexsha == 'a71cdc161b0d87e7ee808f5078ed5fefab758773'][0]
        parent = commit.parents[0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        commit_tests = Main.test_parser.get_tests(module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_not_compiling_testcase = [t for t in commit_testcases if 'MainTest#gooTest' in t.mvn_name][0]
        commit_new_testcases = Main.get_delta_testcases(commit_testcases)
        Main.prepare_project_repo_for_testing(parent, module_path)
        patched_testcases = Main.patch_testcases(commit_testcases, commit, parent, module_path)[0]
        not_compiling_testcases = [t for t in commit_new_testcases if not t in patched_testcases]
        self.assertTrue(not expected_not_compiling_testcase in not_compiling_testcases,
                        "'MainTest#gooTest should have been picked as for compilation error")
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        parent_tests = Main.test_parser.get_tests(module_path)
        parent_testcases = Main.test_parser.get_testcases(parent_tests)
        self.assertTrue(len(parent_testcases) > 0,
                        'Build probably failed')
        self.assertTrue(not expected_not_compiling_testcase in parent_testcases,
                        expected_not_compiling_testcase.mvn_name + ' should have been unpatched')

    def test_patch_tescases_not_compiling_testcases_exclusive_patching(self):
        print('test_patch_tescases_not_compiling_testcases_exclusive_patching')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        commit = [c for c in Main.all_commits if c.hexsha == 'e4d2bb8efdfa576632b99d0e91b35cf0262e70be'][0]
        parent = commit.parents[0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_2'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        commit_tests = Main.test_parser.get_tests(module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_not_compiling_delta_testcase = [t for t in commit_testcases if 'p_1.AssafTest#notCompTest' in t.mvn_name][0]
        expected_compiling_delta_testcase = [t for t in commit_testcases if 'p_1.AssafTest#compTest' in t.mvn_name][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        delta_testcases = Main.get_delta_testcases(commit_testcases)
        patched_testcases = Main.patch_testcases(commit_testcases, commit, parent, module_path)[0]
        not_compiling_testcases = [t for t in delta_testcases if not t in patched_testcases]
        self.assertTrue(expected_not_compiling_delta_testcase in not_compiling_testcases,
                        "'p_1.AssafTest#notCompTest' should have been picked for compilation error")
        self.assertTrue(not expected_not_compiling_delta_testcase in patched_testcases,
                        "'p_1.AssafTest#notCompTest' should have not benn patched")
        self.assertTrue(expected_compiling_delta_testcase in patched_testcases,
                        "'p_1.AssafTest#compTest' should have been patched")
        self.assertTrue(not expected_compiling_delta_testcase in not_compiling_testcases,
                        "'p_1.AssafTest#compTest' should have been patched")

    def test_get_bug_patches_1(self):
        print('test_get_bug_patches_1')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        test_dir =os.path.join( os.getcwd(),r'test_files/test_get_bug_patches')
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        else:
            shutil.rmtree(test_dir)
            os.makedirs(test_dir)
        commit = [c for c in Main.all_commits if c.hexsha == 'e4d2bb8efdfa576632b99d0e91b35cf0262e70be'][0]
        parent = commit.parents[0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_2'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        commit_tests = Main.test_parser.get_tests(module_path)
        dict = {}
        for testclass in commit_tests:
            dict[testclass.id] = test_dir
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_not_compiling_delta_testcase = [t for t in commit_testcases if 'p_1.AssafTest#notCompTest' in t.mvn_name][0]
        expected_compiling_delta_testcase = [t for t in commit_testcases if 'p_1.AssafTest#compTest' in t.mvn_name][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        delta_testcases = Main.get_delta_testcases(commit_testcases)
        patched_testcases = Main.patch_testcases(commit_testcases, commit, parent, module_path)[0]
        dict_test_case_patch = Main.get_bug_patches(patched_testcases, dict)
        patch_file_path = expected_compiling_delta_testcase.src_path
        expected_patched_file_path =os.path.join(test_dir,'expected.java')
        shutil.copyfile(patch_file_path, expected_patched_file_path)
        Main.prepare_project_repo_for_testing(parent, module_path)
        Main.git_cmds_wrapper(lambda: Main.repo.git.execute(['git', 'apply', dict_test_case_patch[expected_compiling_delta_testcase.id]]))
        result_patched_file_path = os.path.join(test_dir, 'result.java')
        shutil.copyfile(patch_file_path, result_patched_file_path)
        self.assertTrue(filecmp.cmp(expected_patched_file_path, result_patched_file_path))
        shutil.rmtree(test_dir)

    def test_get_bug_patches_2(self):
        print('test_get_bug_patches_2')
        Main.set_up(['', 'https://github.com/apache/tika'])
        test_dir =os.path.join( os.getcwd(),r'test_files/test_get_bug_patches_2')
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        else:
            shutil.rmtree(test_dir)
            os.makedirs(test_dir)
        commit = [c for c in Main.all_commits if c.hexsha == 'b12c01d9b56053554cec501aab0530f7f4352daf'][0]
        parent = commit.parents[0]
        module_path = os.getcwd() + r'\tested_project\tika'
        Main.prepare_project_repo_for_testing(commit, module_path)
        os.system(
            'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
        commit_tests = Main.test_parser.get_tests(module_path)
        dict = {}
        for testclass in commit_tests:
            dict[testclass.id] = test_dir
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_delta_testcase = [t for t in commit_testcases if 'testCaseSensitivity' in t.mvn_name][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        delta_testcases = Main.get_delta_testcases(commit_testcases)
        patched_testcases = Main.patch_testcases(commit_testcases, commit, parent, module_path)[0]
        dict_test_case_patch = Main.get_bug_patches(patched_testcases, dict)
        patch_file_path = expected_delta_testcase.src_path
        expected_patched_file_path =os.path.join(test_dir,'expected.java')
        shutil.copyfile(patch_file_path, expected_patched_file_path)
        Main.prepare_project_repo_for_testing(parent, module_path)
        Main.git_cmds_wrapper(lambda: Main.repo.git.execute(['git', 'apply', dict_test_case_patch[expected_delta_testcase.id]]))
        result_patched_file_path = os.path.join(test_dir, 'result.java')
        shutil.copyfile(patch_file_path, result_patched_file_path)
        self.assertTrue(filecmp.cmp(expected_patched_file_path, result_patched_file_path))

    @unittest.skip("Coupled with patch_testcases")
    def test_get_uncompiled_testcases(self):
        print('test_get_compilation_error_testcases')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        commit = [c for c in Main.all_commits if c.hexsha == 'a71cdc161b0d87e7ee808f5078ed5fefab758773'][0]
        parent = commit.parents[0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        commit_tests = Main.test_parser.get_tests(module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_not_compiling_testcase = [t for t in commit_testcases if 'MainTest#gooTest' in t.mvn_name][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        delta_testcases = Main.get_delta_testcases(commit_testcases)
        compilation_error_testcases = Main.get_uncompiled_testcases([delta_testcases])
        self.assertTrue(expected_not_compiling_testcase in compilation_error_testcases,
                        "'MainTest#gooTest should have been picked as for compilation error")

    def test_extract_bugs_1(self):
        print('test_extract_bugs')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        issue = Main.jira.issue('TIKA-19')
        exp_testcase_id = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_fooTest()'
        commit = [c for c in Main.all_commits if c.hexsha == '19f6c78889f9e929bc964d420315a043b62c7967'][0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        tests_paths = Main.get_tests_paths_from_commit(commit)
        res = Main.extract_bugs(issue, commit, tests_paths)
        for bug in res:
            if bug.valid==True and bug.bugged_testcase.id == exp_testcase_id and bug.type == my_bug.Bug_type.DELTA:
                return
        self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

    def test_extract_bugs_2(self):
        print('test_extract_bugs_2')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        issue = Main.jira.issue('TIKA-19')
        exp_testcase_id = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_fooTest()'
        commit = [c for c in Main.all_commits if c.hexsha == '19f6c78889f9e929bc964d420315a043b62c7967'][0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        tests_paths = Main.get_tests_paths_from_commit(commit)
        res = Main.extract_bugs(issue, commit, tests_paths)
        for bug in res:
            if bug.valid and bug.bugged_testcase.id == exp_testcase_id and bug.type == my_bug.Bug_type.DELTA:
                return
        self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

    def test_extract_bugs_pick_up_failures(self):
        print('test_extract_bugs_pick_up_failures')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        issue = Main.jira.issue('TIKA-19')
        exp_testcase_id = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_RTerrorTest()'
        commit = [c for c in Main.all_commits if c.hexsha == '1d3c81c1f7a4722408264cc5279df7abb22a3c04'][0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        tests_paths = Main.get_tests_paths_from_commit(commit)
        res = Main.extract_bugs(issue, commit, tests_paths)
        for bug in res:
            if not bug.valid and bug.bugged_testcase.id == exp_testcase_id and bug.type==my_bug.Bug_type.REGRESSION\
                and bug.desctiption.startswith(my_bug.invalid_rt_error_desc):
                return
        self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

    def test_extract_bugs_delta_testcases_that_passed_in_parrent(self):
        print('test_extract_bugs_pick_up_failures')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        issue = Main.jira.issue('TIKA-19')
        exp_testcase_id = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_deltaPassedTest()'
        commit = [c for c in Main.all_commits if c.hexsha == 'd03e45c84ad903435fae8f1814a56569906663eb'][0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        tests_paths = Main.get_tests_paths_from_commit(commit)
        res = Main.extract_bugs(issue, commit, tests_paths)
        for bug in res:
            if not bug.valid and bug.bugged_testcase.id == exp_testcase_id and bug.type==my_bug.Bug_type.DELTA\
                    and bug.desctiption == my_bug.invalid_passed_desc:
                return
        self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

    @unittest.skip('Not handled yey')
    def test_extract_bugs_pick_up_failures_change_inly_in_src(self):
        print('test_extract_bugs_pick_up_failures')
        Main.set_up(['', 'https://github.com/rotba/GitMavenTrackingProject'])
        issue = Main.jira.issue('TIKA-19')
        exp_testcase_id = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_RTerrorTest()'
        commit = [c for c in Main.all_commits if c.hexsha == '5fb9ab18c99088ecad3f67df97c2bc530180a499'][0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        tests_paths = Main.get_tests_paths_from_commit(commit)
        res = Main.extract_bugs(issue, commit, tests_paths)[0]
        for bug in res:
            if bug.bugged_testcase.id == exp_testcase_id and bug.desctiption == my_bug.invalid_delta_rt_error_desc:
                return
        self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

    def test_get_commit_created_testcases(self):
        print('test_get_commit_created_testcases')
        Main.set_up(['','https://github.com/rotba/GitMavenTrackingProject'])
        exp_test_src_patch = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1\src\test\java\MainTest.java'
        commit = [c for c in Main.all_commits if c.hexsha == '1fd244f006c96fa820efa850f5f31e3f9a727d84'][0]
        parent = commit.parents[0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        tests = Main.test_parser.get_tests(module_path)
        testcases = Main.test_parser.get_testcases(tests)
        Main.prepare_project_repo_for_testing(parent, module_path)
        new_testcases = Main.get_delta_testcases(testcases)
        expected_new_testcase = [t for t in testcases if 'MainTest#foo_2' in t.mvn_name][0]
        self.assertTrue(expected_new_testcase in new_testcases, 'MainTest#foo_2 should be picked for being new test')

    def test_generated_data(self):
        print('test_generated_data')
        Main.USE_CACHE=False
        Main.GENERATE_DATA = True
        Main.main(['','https://github.com/apache/tika','http:\issues.apache.org\jira\projects\TIKA','TIKA-56'])
        expected_issue_dir = os.path.join(Main.data_dir,'TIKA-56')
        expected_commit_dir = os.path.join(expected_issue_dir, 'b12c01d9b56053554cec501aab0530f7f4352daf')
        expected_testclass_dir = os.path.join(expected_commit_dir, 'tika#org.apache.tika.mime.TestMimeTypes')
        expected_testcase_pickle = os.path.join(expected_testclass_dir, 'testCaseSensitivity.pickle')
        expected_report_xml = os.path.join(expected_testclass_dir, 'TEST-org.apache.tika.mime.TestMimeTypes.xml')
        expected_patch = os.path.join(expected_testclass_dir, 'patch.patch')
        self.assertTrue(os.path.isdir(expected_issue_dir))
        self.assertTrue(os.path.isdir(expected_commit_dir))
        self.assertTrue(os.path.isdir(expected_testclass_dir))
        self.assertTrue(os.path.isfile(expected_testcase_pickle))
        self.assertTrue(os.path.isfile(expected_report_xml))
        self.assertTrue(os.path.isfile(expected_patch))
        # shutil.rmtree(Main.data_dir)


if __name__ == '__main__':
    unittest.main()
