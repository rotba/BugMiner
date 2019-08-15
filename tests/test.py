import filecmp
import os
import shutil
import time
import unittest

from PossibleBugMiner.jira_extractor import JiraExtractor
from jira import JIRA
from patcher.patcher import TestcasePatcher

jira = JIRA(options={'server': 'https://issues.apache.org/jira'})

import git

import Main


class TestMain(unittest.TestCase):

	def setUp(self):
		Main.GENERATE_DATA = False
		Main.USE_CACHE = False
		Main.GENERATE_TESTS = False
		Main.branch_inspected = 'master'
		Main.TESTS_GEN_STRATEGY = Main.TestGenerationStrategy.MAVEN

	def tearDown(self):
		pass

	def test_check_out_and_get_tests_from_commit(self):
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		possible_bugs_extractor = JiraExtractor(
			repo_dir=Main.repo.working_dir, branch_inspected=Main.branch_inspected, jira_url=''
		)
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == '52e80f56a2f2877ff2261889b1dc180c51b72f6b'][0]
		tests_paths = possible_bugs_extractor.get_tests_paths_from_commit(commit)
		tests = list(map(lambda t_path: Main.TestObjects.TestClass(t_path), tests_paths))
		self.assertEqual(len(tests), 1,
		                 'Only one test should be associated with 52e80f56a2f2877ff2261889b1dc180c51b72f6b')
		self.assertTrue('NaimTest' in tests[0].mvn_name,
		                '\'NaimTest\' should be associated with 52e80f56a2f2877ff2261889b1dc180c51b72f6b')

	@unittest.skip("Null test")
	def test_created_test_extract_bugs(self):
		print('test_created_test_extract_bugs')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		self.issue_19 = jira.issue('TIKA-19')
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == '52e80f56a2f2877ff2261889b1dc180c51b72f6b'][0]
		tests_paths = Main.get_tests_paths_from_commit(commit)
		res = Main.extract_bugs(self.issue_19, commit, tests_paths)
		for bug in res:
			if bug.commit.hexsha == '52e80f56a2f2877ff2261889b1dc180c51b72f6b' and 'NaimTest#newGooTest' in bug.bugged_testcase.mvn_name and bug.msg == 'Created in test':
				return
		self.fail('Did not extracted bug : created test - \'NaimTest#newGooTest\'')

	def test_find_test_cases_diff(self):
		print('test_find_test_cases_diff')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == '14ef5aa7f71f2beb78f38227399ec4b3388b4127'][0]
		test_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_2\src\test\java\p_1\AssafTest.java'
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_2'
		Main.prepare_project_repo_for_testing(commit, module_path)
		os.system(
			'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
		test = Main.TestObjects.TestClass(test_path)
		expected_delta_testcase = [t for t in test.testcases if 'p_1.AssafTest#goo' in t.mvn_name][0]
		Main.prepare_project_repo_for_testing(commit.parents[0], module_path)
		diff_testcases = Main.find_test_cases_diff(test, test.src_path)
		self.assertTrue(expected_delta_testcase in diff_testcases)

	@unittest.skip("commit_created_testclasses() was deleted")
	def test_get_commit_created_testclasses(self):
		print('test_get_commit_created_testclasses')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == 'e00037324027af30134ee1554b93f5969f8f100e'][0]
		test_report_path = os.getcwd() + 'r\tested_project\MavenProj\sub_mod_1\target\surefire-reports\TEST-p_1.AmitTest.xml'
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		Main.prepare_project_repo_for_testing(commit, module_path)
		os.system(
			'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
		commit_tests = Main.mvn_repo.get_tests(module_path)
		expected_delta_testclass = [t for t in commit_tests if 'p_1.AmitTest' in t.mvn_name][0]
		Main.prepare_project_repo_for_testing(commit.parents[0], module_path)
		diff_testclasses = Main.get_commit_created_testclasses(commit_tests)
		self.assertTrue(expected_delta_testclass in diff_testclasses)


	def test_get_bug_patches_1(self):
		print('test_get_bug_patches_1')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		test_dir = os.path.join(os.getcwd(), r'test_files/test_get_bug_patches')
		if not os.path.exists(test_dir):
			os.makedirs(test_dir)
		else:
			shutil.rmtree(test_dir)
			os.makedirs(test_dir)
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == 'e4d2bb8efdfa576632b99d0e91b35cf0262e70be'][0]
		parent = commit.parents[0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_2'
		Main.prepare_project_repo_for_testing(commit, module_path)
		os.system(
			'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
		commit_tests = Main.mvn_repo.get_tests(module_path)
		dict = {}
		for testclass in commit_tests:
			dict[testclass.id] = test_dir
		commit_testcases = Main.mvn.get_testcases(commit_tests)
		expected_not_compiling_delta_testcase = \
			[t for t in commit_testcases if 'p_1.AssafTest#notCompTest' in t.mvn_name][0]
		expected_compiling_delta_testcase = [t for t in commit_testcases if 'p_1.AssafTest#compTest' in t.mvn_name][0]
		Main.prepare_project_repo_for_testing(parent, module_path)
		delta_testcases = Main.get_delta_testcases(commit_testcases)
		patched_testcases = TestcasePatcher(testcases=commit_testcases, proj_dir=Main.repo.working_dir,
		                                    commit_bug=parent, commit_fix=commit, generated_tests_diff=[],
		                                    gen_commit=None, module_path=module_path).patch().get_patched()
		dict_test_case_patch = Main.get_bug_patches(patched_testcases, dict)
		patch_file_path = expected_compiling_delta_testcase.src_path
		expected_patched_file_path = os.path.join(test_dir, 'expected.java')
		shutil.copyfile(patch_file_path, expected_patched_file_path)
		Main.prepare_project_repo_for_testing(parent, module_path)
		Main.git_cmds_wrapper(
			lambda: Main.repo.git.execute(['git', 'apply', dict_test_case_patch[expected_compiling_delta_testcase.id]]))
		result_patched_file_path = os.path.join(test_dir, 'result.java')
		shutil.copyfile(patch_file_path, result_patched_file_path)
		self.assertTrue(filecmp.cmp(expected_patched_file_path, result_patched_file_path))
		shutil.rmtree(test_dir)

	def test_get_bug_patches_2(self):
		print('test_get_bug_patches_2')
		Main.set_up(['', 'https://github.com/apache/tika'])
		test_dir = os.path.join(os.getcwd(), r'test_files/test_get_bug_patches_2')
		if not os.path.exists(test_dir):
			os.makedirs(test_dir)
		else:
			shutil.rmtree(test_dir)
			os.makedirs(test_dir)
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == 'b12c01d9b56053554cec501aab0530f7f4352daf'][0]
		parent = commit.parents[0]
		module_path = os.getcwd() + r'\tested_project\tika'
		Main.prepare_project_repo_for_testing(commit, module_path)
		os.system(
			'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
		commit_tests = Main.mvn_repo.get_tests(module_path)
		dict = {}
		for testclass in commit_tests:
			dict[testclass.id] = test_dir
		commit_testcases = Main.mvn.get_testcases(commit_tests)
		expected_delta_testcase = [t for t in commit_testcases if 'testCaseSensitivity' in t.mvn_name][0]
		Main.prepare_project_repo_for_testing(parent, module_path)
		delta_testcases = Main.get_delta_testcases(commit_testcases)
		patched_testcases = TestcasePatcher(testcases=commit_testcases, proj_dir=Main.repo.working_dir,
		                                    commit_bug=parent, commit_fix=commit, generated_tests_diff=[],
		                                    gen_commit=None, module_path=module_path).patch().get_patched()
		dict_test_case_patch = Main.get_bug_patches(patched_testcases, dict)
		patch_file_path = expected_delta_testcase.src_path
		expected_patched_file_path = os.path.join(test_dir, 'expected.java')
		shutil.copyfile(patch_file_path, expected_patched_file_path)
		Main.prepare_project_repo_for_testing(parent, module_path)
		Main.git_cmds_wrapper(
			lambda: Main.repo.git.execute(['git', 'apply', dict_test_case_patch[expected_delta_testcase.id]]))
		result_patched_file_path = os.path.join(test_dir, 'result.java')
		shutil.copyfile(patch_file_path, result_patched_file_path)
		self.assertTrue(filecmp.cmp(expected_patched_file_path, result_patched_file_path))

	@unittest.skip("Coupled with patch_testcases")
	def test_get_uncompiled_testcases(self):
		print('test_get_compilation_error_testcases')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == 'a71cdc161b0d87e7ee808f5078ed5fefab758773'][0]
		parent = commit.parents[0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		Main.repo.git.reset('--hard')
		Main.repo.git.checkout(commit.hexsha)
		commit_tests = Main.mvn_repo.get_tests(module_path)
		commit_testcases = Main.mvn_repo.get_testcases(commit_tests)
		expected_not_compiling_testcase = [t for t in commit_testcases if 'MainTest#gooTest' in t.mvn_name][0]
		Main.prepare_project_repo_for_testing(parent, module_path)
		delta_testcases = Main.get_delta_testcases(commit_testcases)
		compilation_error_testcases = Main.get_uncompiled_testcases([delta_testcases])
		self.assertTrue(expected_not_compiling_testcase in compilation_error_testcases,
		                "'MainTest#gooTest should have been picked as for compilation error")

	def test_extract_bugs_1(self):
		print('test_extract_bugs_1')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		possible_bugs_extractor = JiraExtractor(
			repo_dir=Main.repo.working_dir, branch_inspected=Main.branch_inspected, jira_url=''
		)
		issue = jira.issue('TIKA-19')
		exp_testcase_id = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_fooTest()'
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == '19f6c78889f9e929bc964d420315a043b62c7967'][0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		Main.repo.git.checkout(commit.hexsha, '-f')
		tests_paths = possible_bugs_extractor.get_tests_paths_from_commit(commit)
		res = Main.extract_bugs(issue, commit, tests_paths)
		for bug in res:
			if bug.valid == True and bug.bugged_testcase.id == exp_testcase_id and bug.type == Main.mvn_bug.Bug_type.DELTA:
				return
		self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

	def test_extract_bugs_2(self):
		print('test_extract_bugs_2')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		possible_bugs_extractor = JiraExtractor(
			repo_dir=Main.repo.working_dir, branch_inspected=Main.branch_inspected, jira_url=''
		)
		issue = jira.issue('TIKA-19')
		exp_testcase_id = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_fooTest()'
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == '19f6c78889f9e929bc964d420315a043b62c7967'][0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		Main.repo.git.reset('--hard')
		Main.repo.git.checkout(commit.hexsha)
		tests_paths = possible_bugs_extractor.get_tests_paths_from_commit(commit)
		res = Main.extract_bugs(issue, commit, tests_paths)
		for bug in res:
			if bug.valid and bug.bugged_testcase.id == exp_testcase_id and bug.type == Main.mvn_bug.Bug_type.DELTA:
				return
		self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

	@unittest.skip("Can be a cool feature. Fix when theres time")
	def test_extract_bugs_4(self):
		print('test_extract_bugs_4')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		issue = jira.issue('TIKA-19')
		exp_testcase_id = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_delta_3_Test()'
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == 'c94e2644725de71039b8f916555176146069a68f'][0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		Main.repo.git.checkout(commit.hexsha, '-f')
		tests_paths = Main.get_tests_paths_from_commit(commit)
		res = Main.extract_bugs(issue, commit, tests_paths)
		for bug in res:
			if bug.valid == True and bug.bugged_testcase.id == exp_testcase_id and bug.type == Main.mvn_bug.Bug_type.DELTA_3:
				return
		self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

	def test_extract_bugs_auto_generated_test_basic_project(self):
		print('test_extract_bugs_5')
		Main.branch_inspected = 'origin/test_extract_bugs_5'
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		Main.USE_CACHED_STATE = False
		issue = jira.issue('TIKA-19')
		possible_bugs_extractor = JiraExtractor(
			repo_dir=Main.repo.working_dir, branch_inspected=Main.branch_inspected, jira_url=''
		)
		exp_testcase_id = [
			os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\.evosuite\best-tests\p_1\Amit_ESTest.java#Amit_ESTest#None_test4()',
			os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\.evosuite\best-tests\p_1\Amit_ESTest.java#Amit_ESTest#None_test04()',
			os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\.evosuite\best-tests\p_1\Amit_ESTest.java#Amit_ESTest#None_test01()',
			os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\.evosuite\best-tests\p_1\Amit_ESTest.java#Amit_ESTest#None_test00()',
			os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\.evosuite\best-tests\p_1\Amit_ESTest.java#Amit_ESTest#None_test0()']
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == '23270ce01dbf36cd0cf2ccc9438dce641822abb8'][0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		Main.repo.git.reset('--hard')
		Main.repo.git.checkout(commit.hexsha, '-f')
		tests_paths = possible_bugs_extractor.get_tests_paths_from_commit(commit)
		Main.GENERATE_TESTS = True
		res = Main.extract_bugs(issue, commit, tests_paths)
		success = False
		num_of_success_bugs = 0
		for bug in res:
			if bug.valid and bug.type == Main.mvn_bug.Bug_type.GEN:
				num_of_success_bugs += 1
		Main.repo.git.add('--all')
		Main.repo.git.checkout('HEAD', '-f')
		if not 0 < num_of_success_bugs <= 3:
			self.fail('Did not extracted the bug of testcase -' + str(exp_testcase_id))

	def test_extract_bugs_pick_up_failures(self):
		print('test_extract_bugs_pick_up_failures')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		issue = jira.issue('TIKA-19')
		possible_bugs_extractor = JiraExtractor(
			repo_dir=Main.repo.working_dir, branch_inspected=Main.branch_inspected, jira_url=''
		)
		exp_testcase_id = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_RTerrorTest()'
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == '1d3c81c1f7a4722408264cc5279df7abb22a3c04'][0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		Main.repo.git.reset('--hard')
		Main.repo.git.checkout(commit.hexsha)
		tests_paths = possible_bugs_extractor.get_tests_paths_from_commit(commit)
		res = Main.extract_bugs(issue, commit, tests_paths)
		for bug in res:
			if not bug.valid and bug.bugged_testcase.id == exp_testcase_id and bug.type == Main.mvn_bug.Bug_type.REGRESSION \
					and bug.desctiption.startswith(Main.mvn_bug.invalid_rt_error_desc):
				return
		self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

	def test_extract_bugs_delta_testcases_that_passed_in_parrent(self):
		print('test_extract_bugs_pick_up_failures')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		issue = jira.issue('TIKA-19')
		possible_bugs_extractor = JiraExtractor(
			repo_dir=Main.repo.working_dir, branch_inspected=Main.branch_inspected, jira_url=''
		)
		exp_testcase_id = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_deltaPassedTest()'
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == 'd03e45c84ad903435fae8f1814a56569906663eb'][0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		Main.repo.git.reset('--hard')
		Main.repo.git.checkout(commit.hexsha)
		tests_paths = possible_bugs_extractor.get_tests_paths_from_commit(commit)
		res = Main.extract_bugs(issue, commit, tests_paths)
		for bug in res:
			if not bug.valid and bug.bugged_testcase.id == exp_testcase_id and bug.type == Main.mvn_bug.Bug_type.DELTA \
					and bug.desctiption == Main.mvn_bug.invalid_passed_desc:
				return
		self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

	@unittest.skip('Not handled yey')
	def test_extract_bugs_pick_up_failures_change_inly_in_src(self):
		print('test_extract_bugs_pick_up_failures')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		issue = jira.issue('TIKA-19')
		exp_testcase_id = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_RTerrorTest()'
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == '5fb9ab18c99088ecad3f67df97c2bc530180a499'][0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		Main.repo.git.reset('--hard')
		Main.repo.git.checkout(commit.hexsha)
		tests_paths = Main.get_tests_paths_from_commit(commit)
		res = Main.extract_bugs(issue, commit, tests_paths)[0]
		for bug in res:
			if bug.bugged_testcase.id == exp_testcase_id and bug.desctiption == Main.mvn_bug.invalid_delta_rt_error_desc:
				return
		self.fail('Did not extracted the bug of testcase -' + exp_testcase_id)

	def test_get_commit_created_testcases(self):
		print('test_get_commit_created_testcases')
		Main.set_up(['', 'https://github.com/rotba/MavenProj'])
		exp_test_src_patch = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1\src\test\java\MainTest.java'
		commit = [c for c in list(Main.repo.iter_commits(Main.branch_inspected)) if
		          c.hexsha == '1fd244f006c96fa820efa850f5f31e3f9a727d84'][0]
		parent = commit.parents[0]
		module_path = os.getcwd() + r'\tested_project\MavenProj'
		Main.repo.git.reset('--hard')
		Main.repo.git.checkout(commit.hexsha)
		tests = Main.mvn_repo.get_tests(module_path)
		testcases = Main.mvn.get_testcases(tests)
		Main.prepare_project_repo_for_testing(parent, module_path)
		new_testcases = Main.get_delta_testcases(testcases)
		expected_new_testcase = [t for t in testcases if 'MainTest#foo_2' in t.mvn_name][0]
		self.assertTrue(expected_new_testcase in new_testcases, 'MainTest#foo_2 should be picked for being new test')

	def test_generate_data(self):
		if os.path.exists(os.path.join(os.getcwd(), 'results')):
			time.sleep(5)
			shutil.rmtree(os.path.join(os.getcwd(), 'results'), ignore_errors=True)
		Main.USE_CACHE = False
		Main.GENERATE_DATA = True
		Main.GENERATE_TESTS = False
		Main.main(['', 'https://github.com/apache/tika', 'http:\issues.apache.org\jira\projects\TIKA', 'TIKA-56'])
		expected_issue_dir = os.path.join(Main.data_dir, 'TIKA-56')
		expected_commit_dir = os.path.join(expected_issue_dir, 'b12c01d9b56053554cec501aab0530f7f4352daf')
		expected_testclass_dir = os.path.join(expected_commit_dir, 'tika#org.apache.tika.mime.TestMimeTypes')
		expected_pom_dir = os.path.join(expected_commit_dir, 'tika#pom')
		expected_pom_patch_file = os.path.join(expected_pom_dir, 'patch.patch')
		expected_testcase_pickle = os.path.join(expected_testclass_dir, 'testCaseSensitivity.pickle')
		expected_report_xml = os.path.join(expected_testclass_dir, 'TEST-org.apache.tika.mime.TestMimeTypes.xml')
		expected_patch = os.path.join(expected_testclass_dir, 'patch.patch')
		self.assertTrue(os.path.isdir(expected_issue_dir))
		self.assertTrue(os.path.isdir(expected_commit_dir))
		self.assertTrue(os.path.isdir(expected_testclass_dir))
		self.assertTrue(os.path.isfile(expected_testcase_pickle))
		self.assertTrue(os.path.isfile(expected_report_xml))
		self.assertTrue(os.path.isfile(expected_patch))
		self.assertTrue(os.path.isfile(expected_pom_patch_file))

	def test_generate_data_auto_generated_tests(self):
		if os.path.exists(os.path.join(os.getcwd(), 'results')):
			time.sleep(5)
			shutil.rmtree(os.path.join(os.getcwd(), 'results'), ignore_errors=True)
		Main.USE_CACHE = False
		Main.GENERATE_DATA = True
		Main.GENERATE_TESTS = True
		Main.main(['', 'https://github.com/apache/tika', 'http:\issues.apache.org\jira\projects\TIKA', 'TIKA-56'])
		expected_issue_dir = os.path.join(Main.data_dir, 'TIKA-56')
		expected_commit_dir = os.path.join(expected_issue_dir, 'b12c01d9b56053554cec501aab0530f7f4352daf')
		expected_testclass_dir = os.path.join(expected_commit_dir, 'tika#org.apache.tika.mime.MimeTypes_ESTest')
		expected_testclass_dir_2 = os.path.join(expected_commit_dir,
		                                        'tika#org.apache.tika.mime.MimeTypes_ESTest_scaffolding')
		expected_report_xml = os.path.join(expected_testclass_dir, 'TEST-org.apache.tika.mime.MimeTypes_ESTest.xml')
		expected_patch = os.path.join(expected_testclass_dir, 'patch.patch')
		expected_patch_2 = os.path.join(expected_testclass_dir_2, 'patch.patch')
		self.assertTrue(os.path.isdir(expected_issue_dir))
		self.assertTrue(os.path.isdir(expected_commit_dir))
		self.assertTrue(os.path.isdir(expected_testclass_dir))
		self.assertTrue(os.path.isdir(expected_testclass_dir_2))
		self.assertTrue(os.path.isfile(expected_report_xml))
		self.assertTrue(os.path.isfile(expected_patch))
		self.assertTrue(os.path.isfile(expected_patch_2))

	def test_generate_data_auto_generated_tests_cmd_strategy(self):
		Main.TESTS_GEN_STRATEGY = Main.TestGenerationStrategy.CMD
		self.test_generate_data_auto_generated_tests()

	def test_generate_matrix(self):
		if os.path.exists(os.path.join(os.getcwd(), 'results')):
			time.sleep(5)
			shutil.rmtree(os.path.join(os.getcwd(), 'results'), ignore_errors=True)
		Main.USE_CACHE = False
		Main.GENERATE_DATA = True
		Main.TRACE = True
		Main.main(
			['', 'https://github.com/apache/commons-math', 'http:\issues.apache.org\jira\projects\MATH', 'MATH-153'])
		expected_issue_dir = os.path.join(Main.data_dir, 'MATH-153')
		expected_commit_dir = os.path.join(expected_issue_dir, '409d56d206891f76a3e751e4dcdcd22a8c898acc')
		expected_testclass_dir = os.path.join(expected_commit_dir,
		                                      'commons-math#org.apache.commons.math.random.RandomDataTest')
		expected_matrix_file = os.path.join(expected_testclass_dir, 'Matrix_testNextLongExtremeValues.txt')
		self.assertTrue(os.path.isfile(expected_matrix_file))

	# shutil.rmtree(Main.data_dir)

	def test_get_bugged_components_1(self):
		repo_path = os.path.join(os.getcwd(), 'tested_project\MavenProj')
		Main.USE_CACHE = False
		Main.GENERATE_DATA = False
		repo = git.Repo(repo_path)
		repo.git.add('.')
		repo.git.clean('-xdf')
		repo.git.checkout('master', '-f')
		commits = list(filter(lambda c: (
				'b9bccfb7a5dc2bf3537d59341ac2622713393065' in c.hexsha or '6553c2aabc39f8749bae6939f4e8c216a0b08050' in c.hexsha),
		                      list(repo.iter_commits())))
		commit_fix = commits[0]
		commit_bug = commits[1]
		Main.repo = repo
		repo.git.add('.')
		repo.git.clean('-xdf')
		repo.git.checkout(commit_bug, '-f')
		changed_methods = Main.get_bugged_components(commit_fix=commit_fix, commit_bug=commit_bug,
		                                             module=os.path.join(repo_path, 'sub_mod_1'))
		self.assertTrue(len(changed_methods) == 2)
		self.assertTrue('Main#int_foo()' in changed_methods)
		self.assertTrue('Main#void_goo()' in changed_methods)

	def test_get_bugged_components_2(self):
		repo_path = os.path.join(os.getcwd(), 'tested_project\MavenProj')
		Main.USE_CACHE = False
		Main.GENERATE_DATA = False
		repo = git.Repo(repo_path)
		repo.git.add('.')
		repo.git.clean('-xdf')
		repo.git.checkout('master', '-f')
		commits = list(filter(lambda c: (
				'2e1ab62576cf3a76067b794bce8a603d3b877309' in c.hexsha or 'c3ce28f10eade94a6ebf2c280c29c432e378be69' in c.hexsha),
		                      list(repo.iter_commits())))
		commit_fix = commits[0]
		commit_bug = commits[1]
		Main.repo = repo
		repo.git.add('.')
		repo.git.clean('-xdf')
		repo.git.checkout(commit_bug, '-f')
		changed_methods = Main.get_bugged_components(commit_fix=commit_fix, commit_bug=commit_bug,
		                                             module=os.path.join(repo_path, 'sub_mod_1'))
		self.assertTrue(len(changed_methods) == 2)
		self.assertTrue('Main#int_foo()' in changed_methods)
		self.assertTrue('Main#void_goo()' in changed_methods)

	# @unittest.skip('Ment to be run manulay')
	def test_issue(self):
		if os.path.exists(os.path.join(os.getcwd(), 'results')):
			time.sleep(5)
			shutil.rmtree(os.path.join(os.getcwd(), 'results'), ignore_errors=True)
		Main.USE_CACHE = False
		Main.GENERATE_DATA = True
		Main.GENERATE_TESTS = True
		Main.USE_CACHED_STATE = False
		Main.TESTS_GEN_STRATEGY = Main.TestGenerationStrategy.CMD
		Main.main(['', 'https://github.com/apache/tika', 'http:\issues.apache.org\jira\projects\TIKA', 'TIKA-391'])

	# @unittest.skip('Ment to be run manulay')
	def test_issue_and_commit(self):
		if os.path.exists(os.path.join(os.getcwd(), 'results')):
			time.sleep(5)
			shutil.rmtree(os.path.join(os.getcwd(), 'results'), ignore_errors=True)
		Main.USE_CACHE = False
		Main.GENERATE_DATA = True
		Main.GENERATE_TESTS = True
		Main.USE_CACHED_STATE = False
		Main.TESTS_GEN_STRATEGY= Main.TestGenerationStrategy.CMD
		issue_key = 'TIKA-391'
		commit_h = '6f48f57a6a0f21e6589a1d512a25574425dcc4cb'
		github = 'https://github.com/apache/tika'
		issue_tracker = 'http:\issues.apache.org\jira\projects\TIKA'
		Main.set_up(['', github])
		extractor = JiraExtractor(
			repo_dir=Main.repo.working_dir, branch_inspected=Main.branch_inspected, jira_url=issue_tracker,
			issue_key=issue_key
		)
		k = extractor.extract_possible_bugs()
		bug = filter(lambda x: commit_h in x[1], extractor.extract_possible_bugs())[0]
		bug_commit = Main.repo.commit(bug[1])
		bugs = Main.extract_bugs(bug[0], bug_commit, bug[2])
		x = 1


if __name__ == '__main__':
	unittest.main()
