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
from git import Repo
from javadiff import diff as java_diff
from termcolor import colored
import string
import random
import settings
from PossibleBugMiner.extractor_factory import ExtractorFactory
from diff import CommitsDiff
from mvnpy import Repo as MavenRepo
from mvnpy import TestObjects
from mvnpy import bug as mvn_bug
from mvnpy import mvn
from mvnpy.Repo import TestGenerationStrategy
from mvnpy.plugins.evosuite.evosuite import TestsGenerationError
from patcher.patcher import TestcasePatcher

branch_inspected = 'origin/master'
repo = None
reg_repo = None
mvn_repo = None  # type: MavenRepo
reg_mvn_repo = None  # type: MavenRepo
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
USE_CACHE = False
USE_CACHED_STATE = False
GENERATE_DATA = True
GENERATE_TESTS = False
TRACE = False
LIMIT_TIME_FOR_BUILD = 180
MAX_CLASSES_TO_GENERATE_TESTS_FOR = 3
TESTS_GEN_STRATEGY = TestGenerationStrategy.EVOSUITER
TESTS_GEN_SEED = None
DEBUG = False
CONFIG = False


def main(argv):
	bug_data_set = []
	set_up(argv)
	speceific_issue = argv[3] if len(argv) > 3 else None
	jql_query = argv[4] if len(argv) > 4 else None
	candidates = ExtractorFactory.create(
		repo_dir=repo.working_dir, branch_inspected=branch_inspected, issue_tracker_url=argv[2],
		issue_key=speceific_issue,
		query=jql_query
	).extract_possible_bugs_wrapper(use_cache=USE_CACHE)
	for candidate in candidates:
		try:
			bugs = extract_bugs(issue=candidate.issue, commit=repo.commit(candidate.fix_commit),
			                    tests_paths=candidate.tests, changed_classes_diffs=candidate.diffed_components)
			if GENERATE_DATA:
				bug_data_handler.add_bugs(bugs)
		except mvn_bug.BugError as e:
			logging.info('BUG ERROR  ' + e.msg + '\n' + traceback.format_exc())
		except TestObjects.TestParserException as e:
			logging.info('TEST PARSER ERROR  ' + e.msg + '\n' + traceback.format_exc())
		except git.exc.GitCommandError as e:
			logging.info('SHOULD NOT HAPPEN GIT ' + str(e) + '\n' + traceback.format_exc())
			logging.info('Resetting repos')
			reset_repos(argv)
		except Exception as e:
			if 'IOError: [Errno 22]' in str(e):
				logging.info('SHOULD NOT HAPPEN EXCEPTION ' + str(e) + '\n' + traceback.format_exc())
				logging.info('Resetting repos')
				reset_repos(argv)
			else:
				logging.info('SHOULD NOT HAPPEN EXCEPTION ' + str(e) + '\n' + traceback.format_exc())


# Returns bugs solved in the given commit regarding the issue, indicated by the tests
def extract_bugs(issue, commit, tests_paths, changed_classes_diffs=[]):
	logging.info("extract_bugs(): working on issue " + issue.key + ' in commit ' + commit.hexsha)
	ans = []
	parent = get_parent(commit)
	if parent == None:
		return ans
	mvn_repo.clean()
	git_cmds_wrapper(lambda: repo.git.add('.'))
	git_cmds_wrapper(lambda: repo.git.checkout(commit.hexsha, '-f'))
	git_cmds_wrapper(lambda: reg_repo.git.add('.'), spec_repo=reg_repo, spec_mvn_repo=reg_mvn_repo)
	git_cmds_wrapper(lambda: reg_repo.git.checkout(parent.hexsha, '-f'), spec_repo=reg_repo, spec_mvn_repo=reg_mvn_repo)
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
			no_report_testcases = []
			gen_commit = None
			if GENERATE_DATA:
				dict_testclass_bug_dir = bug_data_handler.set_up_bug_dir(
					issue, commit, commit_tests_object, module=module, root_module=mvn_repo.repo_dir
				)
			if CONFIG:
				mvn_repo.config(module=module)
			module_changed_classes = get_most_chenged_classes(module, changed_classes_diffs, commit, parent)
			if GENERATE_TESTS:
				debug_blue('### Generating tests ###')
				if not USE_CACHED_STATE:
					if len(module_changed_classes) == 0: raise mvn_bug.NoAssociatedChangedClasses(
						msg='No classes associated this module')
					gen_report = mvn_repo.generate_tests(
						classes=module_changed_classes, module=module, seed=TESTS_GEN_SEED,
						strategy=TESTS_GEN_STRATEGY, regression_repo=reg_mvn_repo
					)
					mvn_repo.clean(module=module)
					debug_regular(gen_report)
					cache_project_state()
				generated_testcases = mvn_repo.get_generated_testcases(module=module)
				if len(generated_testcases) == 0:
					raise TestsGenerationError(msg='Generated no tests', report=gen_report)
				commit_tests_object += set(list(map(lambda t: t.parent, generated_testcases)))
				dict_modules_testcases[module] += generated_testcases
				if GENERATE_DATA:
					dict_testclass_bug_dir.update(bug_data_handler.cast_tests(issue, commit, commit_tests_object))

			gen_commit_valid_testcases = filter(lambda x: x in commit_valid_testcases, commit_valid_testcases)
			if GENERATE_TESTS:
				mvn_repo.config_for_evosuite(module=module)
				debug_blue('### Running generated tests ###')
				build_log = run_mvn_tests(set(map(lambda t: t.parent, dict_modules_testcases[module])), module)
				debug_regular(build_log)
				(gen_commit_valid_testcases, gen_no_report_testcases) = attach_reports(dict_modules_testcases[module])
				mvn_repo.evosuite_clean(module=module)
				git_cmds_wrapper(lambda: repo.git.add('.'))
				git_cmds_wrapper(lambda: repo.git.commit('-m', 'GARBAGE_COMMIT'))
				generated_tests_diffs = filter(lambda x: is_evosuite_generated_test_file(x.a_path), parent.diff('HEAD'))
				gen_commit = repo.commit(repo.head.commit.hexsha)
				commit_valid_testcases = gen_commit_valid_testcases
				no_report_testcases += gen_no_report_testcases
			else:
				debug_green('### Running tests in commit ###')
				mvn_repo.change_surefire_ver(surefire_version)
				build_log = run_mvn_tests(pick_tests(dict_modules_testcases[module], module), module)
				debug_regular(build_log)
				(commit_valid_testcases, no_report_testcases) = attach_reports(dict_modules_testcases[module])
			gen_commit_valid_testcases = filter(lambda x: x in commit_valid_testcases, commit_valid_testcases)
			if len(commit_valid_testcases) == 0:
				raise mvn.MVNError(msg='No reports', report=build_log, trace=traceback.format_exc())
			git_cmds_wrapper(lambda: repo.git.checkout(parent.hexsha, '-f'))
			delta_testcases = get_delta_testcases(dict_modules_testcases[module])
			debug_green('### Patching delta testcases###')
			if GENERATE_TESTS:
				mvn_repo.setup_tests_generator(module)
			patch = TestcasePatcher(testcases=commit_valid_testcases, commit_fix=commit, commit_bug=parent,
			                        module_path=module, proj_dir=repo.working_dir,
			                        generated_tests_diff=generated_tests_diffs, gen_commit=gen_commit).patch()
			if GENERATE_DATA:
				dict_testcase_patch = get_bug_patches(patch.get_patched(), dict_testclass_bug_dir)
			for unpatchable_testcase in patch.get_all_unpatched():
				ans.append(mvn_bug.Bug(issue_key=issue.key, parent_hexsha=parent.hexsha, commit_hexsha=commit.hexsha,
				                       bugged_testcase=unpatchable_testcase, fixed_testcase=unpatchable_testcase,
				                       type=mvn_bug.determine_type(unpatchable_testcase, delta_testcases,
				                                                   generated_testcases), valid=False,
				                       desc=mvn_bug.invalid_comp_error_desc))
			for no_report_testcase in no_report_testcases:
				ans.append(mvn_bug.Bug(issue_key=issue.key, parent_hexsha=parent.hexsha, commit_hexsha=commit.hexsha,
				                       bugged_testcase=no_report_testcase, fixed_testcase=no_report_testcase,
				                       type=mvn_bug.determine_type(no_report_testcase, delta_testcases,
				                                                   gen_commit_valid_testcases), valid=False,
				                       desc='No report'))
			if GENERATE_TESTS:
				debug_blue('### Running generated tests in parent ###')
				mvn_repo.config_for_evosuite(module)
				build_report = run_mvn_tests(set(
					map(lambda t: t.parent,
					    filter(lambda x: mvn_repo.is_generated_test(x.parent), patch.get_patched()))), module
				)
				debug_regular(build_report)
			else:
				debug_green('### Running tests in parent ###')
				mvn_repo.change_surefire_ver(surefire_version)
				if CONFIG:
					mvn_repo.config(module=module)
				build_report = run_mvn_tests(pick_tests(dict_modules_testcases[module], module), module)
				debug_regular(build_report)
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
					                         bugged_components=module_changed_classes
					                         )
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
				bug_data_handler.add_time(issue.key, commit.hexsha, module, end_time - start_time, mvn_repo.repo_dir)
		except mvn_bug.BugError as e:
			end_time = time.time()
			logging.info('failed inspecting module : ' + module + '. The reason is: ' + e.msg)
			if GENERATE_DATA:
				bug_data_handler.add_time(issue.key, commit.hexsha, module, end_time - start_time,
				                          mvn_repo.repo_dir, 'Failed - ' + e.msg + '\n' + traceback.format_exc())
		except TestsGenerationError as e:
			end_time = time.time()
			logging.info('Tests generation problem! failed inspecting module : ' + module)
			logging.info(traceback.format_exc())
			if GENERATE_DATA:
				bug_data_handler.add_time(issue.key, commit.hexsha, module, end_time - start_time,
				                          mvn_repo.repo_dir, 'Failed:\n ' + str(e))
		except mvn.MVNTimeoutError as e:
			end_time = time.time()
			logging.info('TIMEOUT! failed inspecting module : ' + module)
			logging.info(traceback.format_exc())
			if GENERATE_DATA:
				bug_data_handler.add_time(issue.key, commit.hexsha, module, end_time - start_time,
				                          mvn_repo.repo_dir, 'Failed: ' + str(e) + '\n' + traceback.format_exc())
		except mvn.MVNError as e:
			end_time = time.time()
			logging.info('failed inspecting module : ' + module)
			logging.info(traceback.format_exc())
			if GENERATE_DATA:
				bug_data_handler.add_time(issue.key, commit.hexsha, module, end_time - start_time,
				                          mvn_repo.repo_dir, 'Failed: ' + str(e) + '\n' + traceback.format_exc())

		except Exception as e:
			end_time = time.time()
			logging.info('failed inspecting module : ' + module)
			logging.info(traceback.format_exc())
			if GENERATE_DATA:
				bug_data_handler.add_time(issue.key, commit.hexsha, module, end_time - start_time,
				                          mvn_repo.repo_dir,
				                          'Unexpected failure: ' + str(e) + '\n' + traceback.format_exc())
			debug_regular('Unexpected failure!')
			debug_regular(traceback.format_exc())

	for b in list(filter(lambda b: b.valid, ans, )):
		logging.info('VALID BUG: ' + str(b))
	for b in list(filter(lambda b: not b.valid, ans)):
		# logging.info('INVALID BUG: ' + str(b))
		pass
	git_cmds_wrapper(lambda: repo.git.reset('--hard'))
	return filter_results(ans)


def get_most_chenged_classes(module, changed_classes_diffs, commit, parent):
	def diff_to_mvn_components(diff):
		file_path = os.path.join(repo.working_tree_dir, diff.file_name)
		return convert_to_mvn_name(class_mvn_name=mvn.generate_mvn_class_names(src_path=file_path), module=module)

	def diff_in_module(diff):
		file_path = os.path.join(repo.working_tree_dir, diff.file_name)
		return is_in_module(class_mvn_name=mvn.generate_mvn_class_names(src_path=file_path), module=module)

	return reduce(
		lambda acc, curr: acc + [curr] if len(acc) < MAX_CLASSES_TO_GENERATE_TESTS_FOR else acc,
		map(
			lambda x: diff_to_mvn_components(x),
			sorted(
				filter(
					lambda y: diff_in_module(y),
					changed_classes_diffs
				),
				key=lambda z: calc_importance_index(z, commit, parent),
				reverse=True
			)
		),
		[]
	)


def calc_importance_index(diff, commit, parent):
	def calc_diffed_methods_associated_to_class_from_all_diffed_methods_percanetage(diff):
		all = java_diff.get_changed_methods(repo.working_dir, commit)
		if len(all) == 0:
			raise mvn_bug.BugError('No changed methods')
		associated_to_class = filter(lambda x: diff.file_name in x, all)
		return float(len(associated_to_class)) / float(len(all))

	return calc_diffed_methods_associated_to_class_from_all_diffed_methods_percanetage(diff)


def filter_results(ans):
	def is_relevant_bug_for_res(bug):
		if not (bug.valid == True or bug.valid == False):
			return False
		if GENERATE_TESTS:
			if not bug.type == mvn_bug.Bug_type.GEN:
				return False
			if '_ESTest_scaffolding' in bug.bugged_testcase.mvn_name:
				return False
		return True

	return filter(
		lambda x: is_relevant_bug_for_res(x),
		ans
	)


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
	if TRACE:
		target = r"c:\temp\traces_temp"
		mvn_repo.run_under_jcov(target, module=module, testcases=testcases)
		build_report = mvn_repo.build_report
	else:
		build_report = mvn_repo.test(tests=testcases, module=module, time_limit=LIMIT_TIME_FOR_BUILD)
	if mvn.has_compilation_error(build_report):
		raise mvn.MVNError(msg='Failed due to compilation error', report=build_report, trace=traceback.format_exc())
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
	commit_diff = CommitsDiff.CommitsDiff(
		commit_a=commit_bug,
		commit_b=commit_fix)
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


def get_chacnged_classes(module, changed_classes_diffs):
	def diff_to_mvn_components(diff):
		file_path = os.path.join(repo.working_tree_dir, diff.file_name)
		return convert_to_mvn_name(class_mvn_name=mvn.generate_mvn_class_names(src_path=file_path), module=module)

	def diff_in_module(diff):
		file_path = os.path.join(repo.working_tree_dir, diff.file_name)
		return is_in_module(class_mvn_name=mvn.generate_mvn_class_names(src_path=file_path), module=module)

	return map(
		lambda x: diff_to_mvn_components(x),
		filter(lambda y: diff_in_module(y), changed_classes_diffs)
	)


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


def is_evosuite_generated_test_file(path):
	return '_ESTest.java' in path or '_ESTest_scaffolding.java' in path


# Returns dictionary that maps patched testcase to its patch
def get_bug_patches(patched_testcases, dict_testclass_dir):
	def pom_patch_exist(module):
		return os.path.isfile(os.path.join(dict_testclass_dir[module], 'patch.patch'))

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
		if not pom_patch_exist(testclass.module):
			ans[testclass.module] = generate_patch(git_dir=mvn_repo.repo_dir, file=mvn_repo.get_pom(testclass.module),
			                                       patch_name='patch',
			                                       target_dir=dict_testclass_dir[testclass.module])
		git_cmds_wrapper(lambda: repo.git.reset())
		for testcase in patched_testcases:
			if testcase in testclass.testcases:
				ans[testcase.id] = patch
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


def is_in_module(class_mvn_name, module):
	return class_mvn_name.startswith(os.path.basename(module))


def convert_to_mvn_name(class_mvn_name, module):
	return re.sub('\#.*', '', class_mvn_name[len(os.path.basename(module) + '#'):])


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
def git_cmds_wrapper(git_cmd, spec_repo=repo, spec_mvn_repo=None, counter = 0):
	spec_mvn_repo = mvn_repo if spec_mvn_repo == None else spec_mvn_repo
	try:
		git_cmd()
	except git.exc.GitCommandError as e:
		debug_red("Git bug:\n{}".format(str(e)))
		if 'Another git process seems to be running in this repository, e.g.' in str(e):
			if counter > 10:
				raise e
			counter+=1
			logging.info(str(e))
			time.sleep(2)
			git_cmds_wrapper(lambda: git_cmd(), spec_repo=spec_repo, spec_mvn_repo=spec_mvn_repo, counter=counter)
		elif 'nothing to commit, working tree clean' in str(e):
			pass
		elif 'Please move or remove them before you switch branches.' in str(e):
			logging.info(str(e))
			git_cmds_wrapper(lambda: spec_repo.index.add('.'), spec_repo=spec_repo, spec_mvn_repo=spec_mvn_repo)
			git_cmds_wrapper(lambda: spec_repo.git.clean('-xdf'), spec_repo=spec_repo, spec_mvn_repo=spec_mvn_repo)
			git_cmds_wrapper(lambda: spec_repo.git.reset('--hard'), spec_repo=spec_repo, spec_mvn_repo=spec_mvn_repo)
			time.sleep(2)
			git_cmds_wrapper(lambda: git_cmd(), spec_repo=spec_repo, spec_mvn_repo=spec_mvn_repo)
		elif 'already exists and is not an empty directory.' in str(e):
			pass
		elif 'warning: squelched' in str(e) and 'trailing whitespace.' in str(e):
			pass
		elif 'Filename too long' in str(e):
			if counter > 10:
				raise e
			counter +=1
			spec_mvn_repo.hard_clean()
			git_cmds_wrapper(lambda: git_cmd(), spec_repo=spec_repo, spec_mvn_repo=spec_mvn_repo, counter=counter)
		else:
			raise e


def generate_state_patch_name(state_label='state'):
	sha = repo.git.rev_parse(repo.head.commit.hexsha, short=5)
	now = datetime.datetime.now().strftime("%m-%d-%Y--%H-%M-%S")
	return '_'.join([state_label, sha, now])


def cache_project_state(state_label=''):
	git_cmds_wrapper(lambda: repo.git.add('.'))
	path_to_patch = os.path.join(state_patches_cache_dir, generate_state_patch_name(state_label) + '.patch')
	os.chdir(repo._working_tree_dir)
	cmd = ' '.join(['git', 'diff-index', 'HEAD', '--binary', '>', path_to_patch])
	os.system(cmd)
	os.chdir(orig_wd)
	git_cmds_wrapper(lambda: repo.git.reset('.'))
	return path_to_patch


def pick_tests(testcases, module):
	if mvn_repo.too_much_testcases_to_generate_cmd(testcases, module):
		logging.info('To manny tests. Filtering in order to execute build\nAmount of tests:{}'.format(len(testcases)))
		if not GENERATE_TESTS:
			return set(
				map(lambda y: y.parent, testcases)
			)
		else:
			return set(
				map(lambda y: y.parent,
				    filter(lambda x: mvn_repo.is_generated_test(x.parent), testcases))
			)
	return testcases


# Returns boolean. Filter the bugs to inspect
def bugs_filter(possible_bug):
	if EARLIEST_BUG > 0:
		key = possible_bug[0]
		number = int(key.split('-')[1])
		return number >= EARLIEST_BUG
	return True


def debug_regular(str):
	if DEBUG:
		logging.info(str)
		print(str)


def debug_green(str):
	if DEBUG:
		logging.info(str)
		print(colored(str, 'green'))


def debug_blue(str):
	if DEBUG:
		logging.info(str)
		print(colored(str, 'blue'))


def debug_red(str):
	if DEBUG:
		logging.info(str)
		print(colored(str, 'red'))

def reset_repos(argv):
	try:
		logging.info('Trying renaiming')
		letters = 'sjhfgasjfahjsgfhjasgfhjasgfncdjs'
		orig_base_dir = os.path.dirname(repo.working_dir)
		reg_base_dir = os.path.dirname(reg_repo.working_dir)
		rename_orig = os.path.join(orig_base_dir, ''.join(random.choice(letters) for i in range(10)))
		rename_reg = os.path.join(reg_base_dir, ''.join(random.choice(letters) for i in range(10)))
		os.rename(repo.working_dir, rename_orig)
		os.rename(reg_repo.working_dir, rename_reg)
		set_up(argv, RESET=True)
		return
	except Exception as e:
		logging.info('Failed renaiming with:  ' + str(e) + '\n' + traceback.format_exc())
	logging.info('Trying deletting')
	shutil.rmtree(repo.working_dir,ignore_errors=True)
	shutil.rmtree(reg_repo.working_dir,ignore_errors=True)
	set_up(argv, RESET=True)

def set_up(argv, RESET = False):
	def clone_repo(base, url, label=''):
		logging.info('Started cloning ' + argv[1] + ' {}'.format(label))
		git_cmds_wrapper(lambda: git.Git(base).init())
		repo_url = url.geturl().replace('\\', '/').replace('////', '//')
		git_cmds_wrapper(
			lambda: git.Git(base).clone(repo_url)
		)
		logging.info('Finshed cloning ' + argv[1] + ' {}'.format(label))

	global dict_key_issue
	global dict_hash_commit
	global reg_repo
	global reg_mvn_repo
	global repo
	global mvn_repo
	global patches_dir
	global proj_results_dir
	global proj_name
	global bug_data_handler
	global cache_dir
	global tmp_files_dir
	global data_dir
	global branch_inspected
	global state_patches_cache_dir
	git_url = urlparse(argv[1])
	proj_name = os.path.basename(git_url.path)
	proj_files = settings.ProjFiles(proj_name)
	cache_dir = proj_files.cache
	state_patches_cache_dir = proj_files.states
	tmp_files_dir = proj_files.tmp
	patches_dir = proj_files.patches
	results_dir = settings.RESULTS_DIR
	proj_results_dir = os.path.join(results_dir, proj_name)
	data_dir = os.path.join(proj_results_dir, 'data')
	if not os.path.isdir(proj_results_dir):
		os.makedirs(proj_results_dir)
	if not os.path.isdir(settings.TESTED_PROJECTS_DIR):
		os.makedirs(settings.TESTED_PROJECTS_DIR)
	if not os.path.isdir(cache_dir):
		os.makedirs(cache_dir)
	if not os.path.isdir(state_patches_cache_dir):
		os.makedirs(state_patches_cache_dir)
	if not os.path.isdir(proj_files.reg):
		os.makedirs(proj_files.reg)
	if not os.path.isdir(tmp_files_dir):
		os.makedirs(tmp_files_dir)
	else:
		shutil.rmtree(tmp_files_dir)
		os.makedirs(tmp_files_dir)
	if GENERATE_DATA and not RESET:
		if os.path.isdir(data_dir):
			raise mvn_bug.BugError('The data currently in the project result dir ({}) will be overwritten.'
			                       ' Please backup it in another directory'.format(proj_results_dir))
		os.makedirs(data_dir)
		bug_data_handler = mvn_bug.Bug_data_handler(data_dir)
	if not RESET:
		LOG_FILENAME = os.path.join(proj_results_dir, 'log.log')
		logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format='%(asctime)s %(message)s')
	clone_repo(proj_files.base, git_url)
	clone_repo(proj_files.reg, git_url, 'regression')
	mvn_repo = MavenRepo.Repo(proj_files.repo)
	repo = Repo(proj_files.repo)
	reg_mvn_repo = MavenRepo.Repo(proj_files.reg_repo)
	reg_repo = Repo(proj_files.reg_repo)
	if not os.path.isdir(cache_dir):
		os.makedirs(cache_dir)
	if branch_inspected == None or branch_inspected == '':
		branch_inspected = repo.branches[0].name


if __name__ == '__main__':
	main(sys.argv)
