import copy
import datetime
import logging
import os
import pickle
import re
import shutil
import sys
import time
import traceback
from functools import reduce
from urlparse import urlparse

import git
import javalang
from PossibleBugMiner.jira_extractor import JiraExtractor
from git import Repo
from mvnpy import Repo as MavenRepo
from mvnpy import TestObjects
from mvnpy import bug as mvn_bug
from mvnpy import mvn
from termcolor import colored

from diff import commitsdiff
from diff.commit import Commit

branch_inspected = ''
repo = None  # type: MavenRepo
mvn_repo = None
proj_name = ''
orig_wd = os.getcwd()
patches_dir = ''
proj_results_dir = ''
cache_dir = ''
data_dir = ''
tmp_files_dir = ''
bug_data_handler = ''
valid_bugs_csv_handler = None
invalid_bugs_csv_handler = None
dict_key_issue = {}
surefire_version = '2.22.0'
evosuite_surefire_version = '2.17'
EARLIEST_BUG = 0
USE_CACHE = False
USE_CACHED_STATE = False
GENERATE_DATA = True
GENERATE_TESTS = True
TRACE = False
LIMIT_TIME_FOR_BUILD = 180


def main(argv):
	bug_data_set = []
	set_up(argv)
	speceific_issue = argv[3] if len(argv) > 3 else None
	possible_bugs = JiraExtractor(
		repo_dir=repo.working_dir, branch_inspected=branch_inspected, jira_url=argv[2], issue_key=speceific_issue
	).extract_possible_bugs()
	for possible_bug in possible_bugs:
		try:
			bugs = extract_bugs(issue=possible_bug[0], commit=repo.commit(possible_bug[1]),
			                    tests_paths=possible_bug[2])
			if GENERATE_DATA:
				bug_data_handler.add_bugs(bugs)
		except mvn_bug.BugError as e:
			logging.info('BUG ERROR  ' + e.msg + '\n' + traceback.format_exc())
		except TestObjects.TestParserException as e:
			logging.info('TEST PARSER ERROR  ' + e.msg + '\n' + traceback.format_exc())
		except git.exc.GitCommandError as e:
			logging.info('SHOULD NOT HAPPEN GIT ' + str(e) + '\n' + traceback.format_exc())
		except Exception as e:
			logging.info('SHOULD NOT HAPPEN EXCEPTION ' + str(e) + '\n' + traceback.format_exc())


# Returns bugs solved in the given commit regarding the issue, indicated by the tests
def extract_bugs(issue, commit, tests_paths):
	logging.info("extract_bugs(): working on issue " + issue.key + ' in commit ' + commit.hexsha)
	ans = []
	parent = get_parent(commit)
	if parent == None:
		return ans
	git_cmds_wrapper(lambda: repo.git.add('.'))
	git_cmds_wrapper(lambda: repo.git.checkout(commit.hexsha, '-f'))
	commit_tests_object = list(map(lambda t_path: TestObjects.TestClass(t_path), tests_paths))
	commit_testcases = mvn.get_testcases(commit_tests_object)
	dict_modules_testcases = divide_to_modules(commit_testcases)
	for module in dict_modules_testcases:
		try:
			start_time = time.time()
			module_bugs = []
			commit_valid_testcases = []
			generated_testcases = []
			generated_tests_diffs = []
			gen_commit = None
			if GENERATE_TESTS:
				print(colored('### Generating tests ###', 'blue'))
				if not USE_CACHED_STATE:
					bugged_classes = list(map(lambda c: re.sub('\#.*', '', c),
					                          get_bugged_components(commit_fix=commit, commit_bug=parent,
					                                                module=module)))
					mvn_repo.generate_tests(classes=bugged_classes, module=module)
					cache_project_state()
				generated_testcases = mvn_repo.get_generated_testcases(module=module)
				commit_tests_object += set(list(map(lambda t: t.parent, generated_testcases)))
				dict_modules_testcases[module] += generated_testcases
			if GENERATE_DATA:
				dict_testclass_bug_dir = bug_data_handler.set_up_bug_dir(issue, commit, commit_tests_object)
			print(colored('### Running tests in commit ###', 'green'))
			mvn_repo.change_surefire_ver(surefire_version)
			build_log = run_mvn_tests(dict_modules_testcases[module], module)
			(commit_valid_testcases, no_report_testcases) = attach_reports(dict_modules_testcases[module])
			gen_commit_valid_testcases = filter(lambda x: x in commit_valid_testcases, commit_valid_testcases)
			if GENERATE_TESTS:
				mvn_repo.change_surefire_ver(evosuite_surefire_version)
				print(colored('### Running generated tests ###', 'blue'))
				build_log = run_mvn_tests(set(map(lambda t: t.parent, dict_modules_testcases[module])), module)
				(gen_commit_valid_testcases, gen_no_report_testcases) = attach_reports(dict_modules_testcases[module])
				# changed_files = set(list(map(lambda x: x.src_path,gen_commit_valid_testcases)))
				# map(lambda x: git_cmds_wrapper(lambda: repo.git.add(x)), changed_files)
				mvn_repo.evosuite_clean(module=module)
				git_cmds_wrapper(lambda: repo.git.add('.'))
				git_cmds_wrapper(lambda: repo.git.commit('-m', 'GARBAGE_COMMIT'))
				generated_tests_diffs = filter(lambda x: is_evosuite_generated_test_file(x.a_path), parent.diff('HEAD'))
				gen_commit = repo.commit(repo.head.commit.hexsha)
				commit_valid_testcases = gen_commit_valid_testcases
				no_report_testcases += gen_no_report_testcases
			if len(commit_valid_testcases) == 0:
				raise mvn.MVNError(msg='No reports', report=build_log)
			git_cmds_wrapper(lambda: repo.git.checkout(parent.hexsha, '-f'))
			delta_testcases = get_delta_testcases(dict_modules_testcases[module])
			print(colored('### Patching delta testcases###', 'green'))
			if GENERATE_TESTS:
				mvn_repo.setup_tests_generator(module)
			(patched_testcases, unpatchable_testcases) = patch_testcases(commit_valid_testcases, commit, parent, module,
			                                                             generated_tests_diffs, gen_commit)
			if GENERATE_DATA:
				dict_testcase_patch = get_bug_patches(patched_testcases, dict_testclass_bug_dir)
			for unpatchable_testcase in unpatchable_testcases:
				ans.append(mvn_bug.Bug(issue_key=issue.key, parent_hexsha=parent.hexsha, commit_hexsha=commit.hexsha,
				                       bugged_testcase=unpatchable_testcase[0], fixed_testcase=unpatchable_testcase[0],
				                       type=mvn_bug.determine_type(unpatchable_testcase[0], delta_testcases,
				                                                   generated_testcases), valid=False,
				                       desc=unpatchable_testcase))
			for no_report_testcase in no_report_testcases:
				ans.append(mvn_bug.Bug(issue_key=issue.key, parent_hexsha=parent.hexsha, commit_hexsha=commit.hexsha,
				                       bugged_testcase=no_report_testcase, fixed_testcase=no_report_testcase,
				                       type=mvn_bug.determine_type(no_report_testcase, delta_testcases,
				                                                   gen_commit_valid_testcases), valid=False,
				                       desc='No report'))
			print(colored('### Running tests in parent ###', 'green'))
			if TRACE:
				mvn_repo.setup_tracer()
			mvn_repo.change_surefire_ver(surefire_version)
			run_mvn_tests(dict_modules_testcases[module], module)
			if GENERATE_TESTS:
				print(colored('### Running generated tests in parent ###', 'blue'))
				mvn_repo.change_surefire_ver(evosuite_surefire_version)
				run_mvn_tests([], module)
			# parent_tests = test_parser.get_tests(module)
			if GENERATE_TESTS:
				all_parent_testcases = mvn_repo.get_generated_testcases(module=module)
			else:
				parent_tests = list(map(lambda t_path: TestObjects.TestClass(t_path), tests_paths))
				all_parent_testcases = mvn.get_testcases(parent_tests)
			relevant_parent_testcases = list(filter(lambda t: t in commit_valid_testcases, all_parent_testcases))
			(parent_valid_testcases, no_report_testcases) = attach_reports(relevant_parent_testcases)
			for no_report_testcase in no_report_testcases:
				ans.append(mvn_bug.Bug(issue_key=issue.key, parent_hexsha=parent.hexsha, commit_hexsha=commit.hexsha,
				                       bugged_testcase=no_report_testcase, fixed_testcase=no_report_testcase,
				                       type=mvn_bug.determine_type(no_report_testcase, delta_testcases,
				                                                   gen_commit_valid_testcases), valid=False,
				                       desc='No report'))
			if GENERATE_DATA:
				bug_data_handler.attach_reports(issue, commit, parent_valid_testcases)
			for testcase in commit_valid_testcases:
				if testcase in parent_valid_testcases:
					parent_testcase = [t for t in parent_valid_testcases if t == testcase][0]
					bug = mvn_bug.create_bug(issue=issue, commit=commit, parent=parent, testcase=testcase,
					                         parent_testcase=parent_testcase,
					                         type=mvn_bug.determine_type(testcase, delta_testcases,
					                                                     generated_testcases),
					                         traces=mvn_repo.get_trace(parent_testcase.mvn_name),
					                         bugged_components=get_bugged_components(commit_fix=commit,
					                                                                 commit_bug=parent, module=module))
					module_bugs.append(bug)
			passed_delta_bugs = list(
				filter(lambda b: b.type == mvn_bug.Bug_type.DELTA and b.desctiption == mvn_bug.invalid_passed_desc,
				       module_bugs))
			passed_delta_testcases = list(map(lambda b: b.bugged_testcase, passed_delta_bugs))
			dict_testcases_files = store_test_files(passed_delta_testcases)
			try:
				if len(passed_delta_bugs) > 0:
					ans += try_grandparents(issue=issue, testcases=passed_delta_testcases,
					                        dict_testcases_files=dict_testcases_files, commit=commit, parent=parent)
			except Exception as e:
				logging.info('SHOULD NOT HAPPEN EXCEPTION DELTA TO THE POWER ' + str(e) + '\n' + traceback.format_exc())
			ans += module_bugs
			end_time = time.time()
			if GENERATE_DATA:
				bug_data_handler.add_time(issue.key, commit.hexsha, os.path.basename(module), end_time - start_time)
		except mvn_bug.BugError as e:
			end_time = time.time()
			logging.info('failed inspecting module : ' + module + '. The reason is: ' + e.msg)
			if GENERATE_DATA:
				bug_data_handler.add_time(issue.key, commit.hexsha, os.path.basename(module), end_time - start_time,
				                          'Failed - ' + e.msg)
		except mvn.MVNError as e:
			end_time = time.time()
			logging.info('failed inspecting module : ' + module)
			if GENERATE_DATA:
				bug_data_handler.add_time(issue.key, commit.hexsha, os.path.basename(module), end_time - start_time,
				                          'Failed: ' + str(e))

	for b in list(filter(lambda b: b.valid, ans, )):
		logging.info('VALID BUG: ' + str(b))
	for b in list(filter(lambda b: not b.valid, ans)):
		logging.info('INVALID BUG: ' + str(b))
	git_cmds_wrapper(lambda: repo.git.reset('--hard'))
	return ans


# Tries to run the tests in grandparents commits
def try_grandparents(issue, parent, commit, testcases, dict_testcases_files):
	ans = []
	testcases_copy = list(map(lambda t: copy.deepcopy(t), testcases))
	i = 0
	typs = [mvn_bug.Bug_type.DELTA_2, mvn_bug.Bug_type.DELTA_3]
	curr_comit = parent
	while i < 2:
		curr_parent = get_parent(curr_comit)
		git_cmds_wrapper(lambda: repo.git.checkout(curr_parent.hexsha, '-f'))
		mvn_repo.change_surefire_ver(surefire_version)
		for testcase in testcases_copy:
			if os.path.isfile(testcase.src_path):
				os.remove(testcase.src_path)
			shutil.copyfile(dict_testcases_files[testcase.id], testcase.src_path)
		run_mvn_tests(testcases_copy, testcases_copy[0].module)
		(grand_parent_valid_testcases, no_report_testcases) = attach_reports(testcases_copy)
		for testcase in testcases:
			if testcase in grand_parent_valid_testcases:
				grand_parent_testcase = [t for t in grand_parent_valid_testcases if t == testcase][0]
				bug = mvn_bug.create_bug(issue=issue, commit=commit, parent=curr_parent, testcase=testcase,
				                         parent_testcase=grand_parent_testcase,
				                         type=typs[i])
				if bug.valid:
					testcases_copy.remove(testcase)
					ans.append(bug)
		if len(testcases_copy) == 0:
			break
		curr_comit = curr_parent
		i += 1

	return ans


# Handles running maven. Will try to run the smallest module possib;e
def run_mvn_tests(testcases, module):
	build_report = mvn_repo.test(tests=testcases, module=module, time_limit=LIMIT_TIME_FOR_BUILD)
	if mvn.has_compilation_error(build_report):
		raise mvn.MVNError(msg='Failed due to compilation error', report=build_report)
	return build_report


# Attaches reports to testcases and returns the testcases that reports were successfully attached to them.
# Handles exceptions, updates invalid_bugs
def attach_reports(testcases):
	attatched = []
	no_attatched = []
	for testcase in testcases:
		testcase.parent.clear_report()
	ans = (attatched, no_attatched)
	for testcase in testcases:
		testclass = testcase.parent
		if testclass.report is None:
			try:
				testclass.report = TestObjects.TestClassReport(testclass.get_report_path(), testclass.module)
				testclass.attach_report_to_testcase(testcase)
				attatched.append(testcase)
			except TestObjects.TestParserException as e:
				for t in testclass.testcases:
					if t in testcases:
						no_attatched.append(t)
				continue
		else:
			try:
				testclass.attach_report_to_testcase(testcase)
				attatched.append(testcase)
			except TestObjects.TestParserException as e:
				logging.info(str(
					e) + ' the testcalss of this testcase had his report attached. So this testcase must have gotten report')
				no_attatched.append(testcase)

	return ans


# Returns a list of methods that are associated with a change in the diff of the commits
def get_bugged_components(commit_fix, commit_bug, module):
	ans = []
	commit_diff = commitsdiff.CommitsDiff(
		commit_a=Commit.init_commit_by_git_commit(commit_bug, 0),
		commit_b=Commit.init_commit_by_git_commit(commit_fix, 0))
	for file_diff in commit_diff.diffs:
		if file_diff.file_name.endswith('.java'):
			file_path = os.path.join(repo.working_tree_dir, file_diff.file_name)
			ans += list(
				map(lambda m: mvn.generate_mvn_class_names(src_path=file_path, module=module) + '#' + m,
				    file_diff.changed_methods)
			)
	return ans


# Returns dictionar mapping testcases to the file currently contains them.
def store_test_files(passed_delta_testcases):
	ans = {}
	for testcase in passed_delta_testcases:
		source = testcase.src_path
		destination = os.path.join(tmp_files_dir, os.path.basename(testcase.src_path))
		if not destination in ans.values():
			shutil.copy2(source, destination)
		ans[testcase.id] = destination
	return ans


# Returns list of testcases that exist in commit_tests and not exist in the current state (commit)
def get_delta_testcases(testcases):
	ans = []
	for testcase in testcases:
		src_path = testcase.src_path
		if os.path.isfile(src_path):
			with open(src_path, 'r') as src_file:
				tree = javalang.parse.parse(src_file.read())
		else:
			ans.append(testcase)
			continue
		class_decls = [class_dec for _, class_dec in tree.filter(javalang.tree.ClassDeclaration)]
		if not any([testcase_in_class(c, testcase) for c in class_decls]):
			ans.append(testcase)
	return ans


# Returns list of testcases that exist in commit_tests and in the current state and are modied(commit)
def get_modified_testcases(testcases):
	ans = []
	for testcase in testcases:
		src_path = testcase.src_path
		if os.path.isfile(src_path):
			testclass = TestObjects.TestClass(src_path)
			if testcase in testclass.testcases:
				tmp = [t for t in testclass.testcases if t == testcase]
				assert len(tmp) == 1
				if not testcase.has_the_same_code(tmp[0]):
					ans.append(testcase)
	return ans


# Patches tests in the project. Returns the patches that didn't generate compilation errors
def patch_testcases(commit_testcases, commit, prev_commit, module_path, generated_tests_diff, gen_commit):
	ans = []
	unpatchable_testcases = []
	dict_diff_testcases = {}
	dict_diff_patch = {}
	dict_file_diff = {}
	not_compiling_testcases = []
	set_up_patches_dir()
	DELETE_ME = set(list((list(commit.diff(prev_commit)) + generated_tests_diff)))
	for diff in set(list((list(commit.diff(prev_commit)) + generated_tests_diff))):
		associeted_testcases = get_associated_test_case(diff, commit_testcases)
		if not len(associeted_testcases) == 0:
			test_path = get_diff_src_path(associeted_testcases, diff)
			target_commit = commit if gen_commit == None else gen_commit
			patch_path = generate_patch(git_dir=mvn_repo.repo_dir, prev_commit=prev_commit,
			                            commit=target_commit, file=test_path,
			                            patch_name=os.path.basename(test_path), target_dir=patches_dir)
			git_cmds_wrapper(lambda: repo.git.execute(['git', 'apply', patch_path]))
			dict_diff_testcases[diff] = associeted_testcases
			dict_diff_patch[diff] = patch_path
			dict_file_diff[test_path] = diff
			ans.extend(associeted_testcases)
	tries = 0
	mvn_repo.clean(module_path)
	build_report = mvn_repo.test_compile(module_path)
	compilation_error_report = mvn.get_compilation_error_report(build_report)
	# if not len(compilation_error_report) == 0:
	while not len(compilation_error_report) == 0 and tries < 2:
		compilation_errors = mvn.get_compilation_errors(compilation_error_report)
		dict_file_errors = divide_errors_to_files(compilation_errors)
		for file in dict_file_errors:
			error_testclass = TestObjects.TestClass(file)
			for error in dict_file_errors[file]:
				if is_unrelated_testcase(error, error_testclass):
					diff = dict_file_diff[error.path]
					git_cmds_wrapper(lambda: repo.git.execute(['git', 'apply', '-R', dict_diff_patch[diff]]))
					for testcase in dict_diff_testcases[diff]:
						unpatchable_testcases.append((testcase,
						                              'Testclass file is not compiling because compilation error not related to testcases: ' + str(
							                              error)))
						ans.remove(testcase)
					continue
				else:
					tmp = [tc for tc in error_testclass.testcases if tc.contains_line(error.line)]
					if not len(tmp) == 1:
						raise mvn_bug.BugError('unexpeced :' + str(tmp))
					unpatchable_testcases.append((tmp[0], 'Generated compilation error'))
					not_compiling_testcases.append(tmp[0])
		still_patched_not_compiling_testcases = list(filter(lambda t: t in ans, not_compiling_testcases))
		unpatch_testcases(still_patched_not_compiling_testcases)
		for testcase in still_patched_not_compiling_testcases:
			ans.remove(testcase)
		not_compiling_testcases = []
		tries += 1
		mvn_repo.clean(module_path)
		build_report = mvn_repo.test_compile(module_path)
		compilation_error_report = mvn.get_compilation_error_report(build_report)
	return (ans, unpatchable_testcases)


def is_evosuite_generated_test_file(path):
	return '_ESTest.java' in path or '_ESTest_scaffolding.java' in path


def get_diff_src_path(associeted_testcases, diff):
	if 'ESTest_scaffolding' in diff.a_path:
		return generate_ESTest_scaffolding_path(associeted_testcases, diff)
	return associeted_testcases[0].src_path


def generate_ESTest_scaffolding_path(associeted_testcases, diff):
	return os.path.normpath(os.path.join(repo.working_dir, diff.a_path))


# Returns dictionary that maps patched testcase to its patch
def get_bug_patches(patched_testcases, dict_testclass_dir):
	ans = {}
	testclasses = []
	for testcase in patched_testcases:
		if not testcase.parent in testclasses:
			testclasses.append(testcase.parent)
	for testclass in testclasses:
		git_cmds_wrapper(lambda: repo.git.add('.'))
		patch = generate_patch(git_dir=mvn_repo.repo_dir, file=testclass.src_path, patch_name='patch',
		                       target_dir=dict_testclass_dir[testclass.id])
		if mvn_repo.is_generated_test(testclass):
			scaffolding_path = testclass.src_path.replace('.java', '_scaffolding.java')
			patch = generate_patch(git_dir=mvn_repo.repo_dir, file=scaffolding_path, patch_name='patch',
			                       target_dir=dict_testclass_dir[testclass.id + '_scaffolding'])
		git_cmds_wrapper(lambda: repo.git.reset())
		for testcase in patched_testcases:
			if testcase in testclass.testcases:
				ans[testcase.id] = patch
	return ans


# Returns true if the given compilation error report object is unrelated to any testcase in it's file
def is_unrelated_testcase(error, error_testclass):
	return not any([t.contains_line(error.line) for t in error_testclass.testcases])


# Returns dictionary mapping file path to it's related compilation error in the given errors
def divide_errors_to_files(compilation_errors):
	ans = {}
	for error in compilation_errors:
		if not error.path in ans.keys():
			ans[error.path] = []
		ans[error.path].append(error)
	return ans


# Removes the testcases from their files
def unpatch_testcases(testcases):
	dict_file_testcases = divide_to_files(testcases)
	for file in dict_file_testcases.keys():
		positions_to_delete = list(map(lambda t: t.get_lines_range(), dict_file_testcases[file]))
		with open(file, 'r') as f:
			lines = f.readlines()
		with open(file, 'w') as f:
			i = 1
			for line in lines:
				if any(p[0] <= i <= p[1] for p in positions_to_delete):
					f.write('')
				else:
					f.write(line)
				i += 1


# Returns dictionary mapping path to group of associated testcases
def divide_to_files(testcases):
	ans = {}
	for testcase in testcases:
		path_to_file = testcase.src_path
		if not path_to_file in ans.keys():
			ans[path_to_file] = []
		ans[path_to_file].append(testcase)
	return ans


# Creates patch representing the changes occured in file between commit and prev_commit
def generate_patch(git_dir, file, patch_name, target_dir, prev_commit=None, commit=None):
	path_to_patch = target_dir + '//' + patch_name + '.patch'
	os.chdir(git_dir)
	if prev_commit == None or commit == None:
		cmd = ' '.join(['git', 'diff', 'HEAD', file, '>', path_to_patch])
	else:
		cmd = ' '.join(['git', 'diff', prev_commit.hexsha, commit.hexsha, file, '>', path_to_patch])
	os.system(cmd)
	os.chdir(orig_wd)
	return path_to_patch


# Checkout to the given commit, cleans the project, and installs the project
def prepare_project_repo_for_testing(commit, module):
	repo.git.add('.')
	git_cmds_wrapper(lambda: repo.git.commit('-m', 'BugDataMiner run'))
	git_cmds_wrapper(lambda: repo.git.checkout(commit.hexsha))
	os.system('mvn clean -f ' + module)


# returns list of patches that didn't compile from
def get_uncompiled_testcases(testcases_diff_groups):
	ans = []
	for testcases_diff_group in testcases_diff_groups:
		associated_file = testcases_diff_group[0].src_path
		mvn_repo.clean(testcases_diff_group[0].module)
		build_report = mvn_repo.test_compile(testcases_diff_group[0].module)
		compilation_error_report = mvn.get_compilation_error_report(build_report)
		if not len(compilation_error_report) == 0:
			error_testcases = mvn.get_compilation_error_testcases(compilation_error_report)
			if any(t.src_path == associated_file for t in error_testcases):
				if len(relevant_error_testcases) == 0:
					raise mvn_bug.BugError(
						'Patching generated compilation error not associated to testcases.' +
						'\nCompilation error report:\n' +
						reduce((lambda x, y: x + '\n' + y), compilation_error_report))
				else:
					ans += relevant_error_testcases
			relevant_error_testcases = list(filter(lambda t: t in testcases_diff_group, error_testcases))
	return ans


# Returns true if file is associated with a test file
def is_test_file(file):
	name = os.path.basename(file.lower())
	if not name.endswith('.java'):
		return False
	if name.endswith('test.java'):
		return True
	if name.startswith('test'):
		return True
	return False


# Returns the parent of the given commit in the inspected branch
def get_parent(commit):
	ans = None
	for curr_parent in commit.parents:
		for branch in curr_parent.repo.refs:
			if branch.name == branch_inspected:
				ans = curr_parent
				break
	return ans


# Returns true if testcase is in class_decl
def testcase_in_class(class_decl, testcase):
	method_names = list(map(lambda m: class_decl.name + '#' + m.name, class_decl.methods))
	return any(testcase.mvn_name.endswith(m_name) for m_name in method_names)


# Returns list of strings describing tests or testcases that are not in module dir
def find_test_cases_diff(commit_test_class, src_path):
	ans = []
	testcases_in_src = []
	if os.path.isfile(src_path):
		with open(src_path, 'r') as src_file:
			tree = javalang.parse.parse(src_file.read())
	else:
		return commit_test_class.testcases
	class_decl = [c for c in tree.children[2] if c.name in commit_test_class.mvn_name][0]
	for method in class_decl.methods:
		testcases_in_src.append(commit_test_class.mvn_name + '#' + method.name)
	for testcase in commit_test_class.testcases:
		i = 0
		for testcase_in_src in testcases_in_src:
			if testcase_in_src in testcase.mvn_name:
				continue
			else:
				i += 1
				if i == len(testcases_in_src):
					ans.append(testcase)
	return ans


# Returns true if the two paths are associated to the same thest
def are_associated_test_paths(path, test_path):
	n_path = os.path.normcase(path)
	n_test_path = os.path.normcase(test_path)
	return n_path in n_test_path or n_path.strip('.evosuite\\best-tests').strip('_scaffolding.java') in n_test_path


# Returns dictionary containing pairs of module and it's associated testcases
def divide_to_modules(tests):
	ans = {}
	for test in tests:
		if not test.module in ans.keys():
			ans[test.module] = []
		ans[test.module].append(test)
	return ans


# Returns list of all the diffs associated with test case
def get_associated_test_case(diff, testcases):
	ans = []
	for testcase in testcases:
		if are_associated_test_paths(diff.a_path, testcase.src_path):
			ans.append(testcase)
	return ans


# Returns data stored in the cache dir. If not found, retrieves the data using the retrieve func
def get_from_cache(cache_file_path, retrieve_func):
	if os.path.isfile(cache_file_path):
		cache_file = open(cache_file_path, 'rb')
		ans = pickle.load(cache_file)
		cache_file.close()
		return ans
	else:
		data = retrieve_func()
		cache_file = open(cache_file_path, 'wb')
		pickle.dump(data, cache_file, protocol=2)
		cache_file.close()
		return data


# Returns true if the commit message contains the issue key exclusively
def is_associated_to_commit(issue, commit):
	if issue.key in commit.message:
		index_of_char_after_issue_key = commit.message.find(issue.key) + len(issue.key)
		if index_of_char_after_issue_key == len(commit.message):
			return True
		char_after_issue_key = commit.message[commit.message.find(issue.key) + len(issue.key)]
		return not char_after_issue_key.isdigit()
	else:
		return False


# Sets up patches dir
def set_up_patches_dir():
	if not os.path.isdir(patches_dir):
		os.makedirs(patches_dir)
	else:
		shutil.rmtree(patches_dir)
		os.makedirs(patches_dir)


# Wraps git command. Handles excpetions mainly
def git_cmds_wrapper(git_cmd):
	try:
		git_cmd()
	except git.exc.GitCommandError as e:
		if 'Another git process seems to be running in this repository, e.g.' in str(e):
			logging.info(str(e))
			time.sleep(2)
			git_cmds_wrapper(lambda: git_cmd())
		elif 'nothing to commit, working tree clean' in str(e):
			pass
		elif 'Please move or remove them before you switch branches.' in str(e):
			logging.info(str(e))
			git_cmds_wrapper(lambda: repo.index.add('.'))
			git_cmds_wrapper(lambda: repo.git.clean('-xdf'))
			git_cmds_wrapper(lambda: repo.git.reset('--hard'))
			time.sleep(2)
			git_cmds_wrapper(lambda: git_cmd())
		elif 'already exists and is not an empty directory.' in str(e):
			pass
		elif 'warning: squelched' in str(e) and 'trailing whitespace.' in str(e):
			pass
		else:
			raise e


def cache_project_state(state_label=''):
	git_cmds_wrapper(lambda: repo.git.add('.'))
	path_to_patch = os.path.join(state_patches_cache_dir, generate_state_patch_name(state_label) + '.patch')
	os.chdir(repo._working_tree_dir)
	cmd = ' '.join(['git', 'diff-index', 'HEAD', '--binary', '>', path_to_patch])
	os.system(cmd)
	os.chdir(orig_wd)
	git_cmds_wrapper(lambda: repo.git.reset('.'))
	return path_to_patch


def generate_state_patch_name(state_label='state'):
	sha = repo.git.rev_parse(repo.head.commit.hexsha, short=5)
	now = datetime.datetime.now().strftime("%m-%d-%Y--%H-%M-%S")
	return '_'.join([state_label, sha, now])


# Returns boolean. Filter the bugs to inspect
def bugs_filter(possible_bug):
	if EARLIEST_BUG > 0:
		key = possible_bug[0]
		number = int(key.split('-')[1])
		return number >= EARLIEST_BUG
	return True


def set_up(argv):
	global dict_key_issue
	global dict_hash_commit
	global repo
	global patches_dir
	global proj_results_dir
	global proj_name
	global bug_data_handler
	global cache_dir
	global tmp_files_dir
	global data_dir
	global branch_inspected
	global mvn_repo
	global state_patches_cache_dir
	git_url = urlparse(argv[1])
	proj_name = os.path.basename(git_url.path)
	cache_dir = os.path.join(os.getcwd(), 'cache\\{}'.format(proj_name))
	state_patches_cache_dir = os.path.join(cache_dir, 'states')
	tmp_files_dir = os.path.join(os.getcwd(), 'tmp_files\\{}'.format(proj_name))
	mvn_repo = MavenRepo.Repo(os.getcwd() + '\\tested_project\\' + proj_name)
	patches_dir = mvn_repo.repo_dir + '\\patches'
	results_dir = os.path.join(os.getcwd(), 'results')
	proj_results_dir = os.path.join(results_dir, proj_name)
	data_dir = os.path.join(proj_results_dir, 'data')
	if not os.path.isdir(proj_results_dir):
		os.makedirs(proj_results_dir)
	if not os.path.isdir(os.getcwd() + '\\tested_project'):
		os.makedirs(os.getcwd() + '\\tested_project')
	if not os.path.isdir(cache_dir):
		os.makedirs(cache_dir)
	if not os.path.isdir(state_patches_cache_dir):
		os.makedirs(state_patches_cache_dir)
	if not os.path.isdir(tmp_files_dir):
		os.makedirs(tmp_files_dir)
	else:
		shutil.rmtree(tmp_files_dir)
		os.makedirs(tmp_files_dir)
	if GENERATE_DATA:
		if os.path.isdir(data_dir):
			raise mvn_bug.BugError('The data currently in the project result dir ({}) will be overwritten.'
			                       ' Please backup it in another directory'.format(proj_results_dir))
		os.makedirs(data_dir)
		bug_data_handler = mvn_bug.Bug_data_handler(data_dir)
	LOG_FILENAME = os.path.join(proj_results_dir, 'log.log')
	logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format='%(asctime)s %(message)s')
	logging.info('Started cloning ' + argv[1] + '... ')
	git_cmds_wrapper(lambda: git.Git(os.getcwd() + '\\tested_project').init())
	repo_url = git_url.geturl().replace('\\', '/').replace('////', '//')
	git_cmds_wrapper(
		lambda: git.Git(os.getcwd() + '\\tested_project').clone(repo_url))
	logging.info('Finshed cloning ' + argv[1] + '...')
	repo = Repo(mvn_repo.repo_dir)
	if not os.path.isdir(cache_dir):
		os.makedirs(cache_dir)
	if branch_inspected == None or branch_inspected == '':
		branch_inspected = repo.branches[0].name


if __name__ == '__main__':
	main(sys.argv);
