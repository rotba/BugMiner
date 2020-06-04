import os
import unittest
from urlparse import urlparse

import git
import javalang
from mvnpy import mvn
from mvnpy.Repo import Repo as MVN_Repo

import patcher
from patcher import TestcasePatcher

REPOS_DIR = 'repos'


class TestcasePatcherTest(unittest.TestCase):
	def setUpProj(self, git_url):
		git_url = urlparse(git_url)
		projects_dir = os.path.join(os.path.join(os.getcwd(), REPOS_DIR))
		proj_dir = os.path.join(projects_dir, os.path.basename(git_url.path))
		if not os.path.isdir(projects_dir):
			os.makedirs(projects_dir)
		patcher.git_cmds_wrapper(lambda: git.Git(projects_dir).init(), None)
		repo_url = git_url.geturl().replace('\\', '/').replace('////', '//')
		patcher.git_cmds_wrapper(
			lambda: git.Git(projects_dir).clone(repo_url), None
		)
		return proj_dir

	def test_patch_tescases(self):
		git_url = 'https://github.com/rotba/MavenProj'
		git_dir = self.setUpProj(git_url=git_url)
		git_repo = git.Repo(git_dir)
		mvn_repo = MVN_Repo(git_dir)
		branch_inspected = 'origin/master'
		hey = list(git_repo.iter_commits(branch_inspected))
		commit = [c for c in list(git_repo.iter_commits(branch_inspected)) if
		          c.hexsha == 'e00037324027af30134ee1554b93f5969f8f100e'][0]
		parent = commit.parents[0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		module_path = os.path.join(mvn_repo.repo_dir, 'sub_mod_1')
		prepare_project_repo_for_testing(commit, module_path, git_repo)
		os.system(
			'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
		commit_tests = mvn_repo.get_tests(module_path)
		commit_testcases = mvn.get_testcases(commit_tests)
		expected_delta_testcase = [t for t in commit_testcases if 'p_1.AmitTest#hoo' in t.mvn_name][0]
		prepare_project_repo_for_testing(parent, module_path, git_repo)
		patcher = TestcasePatcher(testcases=commit_testcases, proj_dir=git_dir, commit_fix=commit, commit_bug=parent,
		                          module_path=module_path, generated_tests_diff=[], gen_commit=None)
		patcher.patch()
		os.system(
			'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
		parent_tests = mvn_repo.get_tests(module_path)
		parent_testcases = mvn.get_testcases(parent_tests)
		self.assertTrue(expected_delta_testcase in parent_testcases,
		                "'p_1.AmitTest should have been patchd on the parent commit and exist")

	def test_patch_tescases_not_compiling_testcases(self):
		git_url = 'https://github.com/rotba/MavenProj'
		commit_h = 'a71cdc161b0d87e7ee808f5078ed5fefab758773'
		git_dir = self.setUpProj(git_url=git_url)
		git_repo = git.Repo(git_dir)
		mvn_repo = MVN_Repo(git_dir)
		branch_inspected = 'origin/master'
		hey = list(git_repo.iter_commits(branch_inspected))
		commit = [c for c in list(git_repo.iter_commits(branch_inspected)) if
		          c.hexsha == commit_h][0]
		parent = commit.parents[0]
		module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
		module_path = os.path.join(mvn_repo.repo_dir, 'sub_mod_1')
		prepare_project_repo_for_testing(commit, module_path, git_repo)
		os.system(
			'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
		commit_tests = mvn_repo.get_tests(module_path)
		commit_testcases = mvn.get_testcases(commit_tests)
		expected_not_compiling_testcase = [t for t in commit_testcases if 'MainTest#gooTest' in t.mvn_name][0]
		commit_new_testcases = get_delta_testcases(commit_testcases)
		prepare_project_repo_for_testing(parent, module_path, git_repo)
		patcher = TestcasePatcher(testcases=commit_testcases, proj_dir=git_dir, commit_fix=commit, commit_bug=parent,
		                          module_path=module_path, generated_tests_diff=[], gen_commit=None)
		patcher.patch()
		not_compiling_testcases = patcher.get_all_unpatched()
		self.assertTrue(expected_not_compiling_testcase in not_compiling_testcases,
		                "'MainTest#gooTest should have been picked as for compilation error")
		os.system(
			'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
		parent_tests = mvn_repo.get_tests(module_path)
		parent_testcases = mvn.get_testcases(parent_tests)
		self.assertTrue(len(parent_testcases) > 0,
		                'Build probably failed')
		self.assertTrue(not expected_not_compiling_testcase in parent_testcases,
		                expected_not_compiling_testcase.mvn_name + ' should have been unpatched')

	def test_patch_tescases_not_compiling_testcases_exclusive_patching(self):
		git_url = 'https://github.com/rotba/MavenProj'
		commit_h = 'e4d2bb8efdfa576632b99d0e91b35cf0262e70be'
		git_dir = self.setUpProj(git_url=git_url)
		git_repo = git.Repo(git_dir)
		mvn_repo = MVN_Repo(git_dir)
		branch_inspected = 'origin/master'
		hey = list(git_repo.iter_commits(branch_inspected))
		commit = [c for c in list(git_repo.iter_commits(branch_inspected)) if
		          c.hexsha == commit_h][0]
		parent = commit.parents[0]
		module_path = os.path.join(mvn_repo.repo_dir, 'sub_mod_2')
		prepare_project_repo_for_testing(commit, module_path, git_repo)
		os.system(
			'mvn clean test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f ' + module_path)
		commit_tests = mvn_repo.get_tests(module_path)
		commit_testcases = mvn.get_testcases(commit_tests)
		expected_not_compiling_delta_testcase = \
			[t for t in commit_testcases if 'p_1.AssafTest#notCompTest' in t.mvn_name][0]
		expected_compiling_delta_testcase = [t for t in commit_testcases if 'p_1.AssafTest#compTest' in t.mvn_name][0]
		prepare_project_repo_for_testing(parent, module_path, git_repo)
		delta_testcases = get_delta_testcases(commit_testcases)
		patcher = TestcasePatcher(testcases=commit_testcases, proj_dir=git_dir, commit_fix=commit, commit_bug=parent,
		                          module_path=module_path, generated_tests_diff=[], gen_commit=None).patch()
		unpatched = patcher.get_all_unpatched()
		patched = patcher.get_patched()
		self.assertTrue(expected_not_compiling_delta_testcase in unpatched,
		                "'p_1.AssafTest#notCompTest' should have been picked for compilation error")
		self.assertTrue(not expected_not_compiling_delta_testcase in patched,
		                "'p_1.AssafTest#notCompTest' should have not benn patched")
		self.assertTrue(expected_compiling_delta_testcase in patched,
		                "'p_1.AssafTest#compTest' should have been patched")
		self.assertTrue(not expected_compiling_delta_testcase in unpatched,
		                "'p_1.AssafTest#compTest' should have been patched")



def prepare_project_repo_for_testing(commit, module, repo):
	repo.git.add('.')
	patcher.git_cmds_wrapper(lambda: repo.git.commit('-m', 'BugDataMiner run'), repo)
	patcher.git_cmds_wrapper(lambda: repo.git.checkout(commit.hexsha), repo)
	os.system('mvn clean -f ' + module)


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


# Returns true if testcase is in class_decl
def testcase_in_class(class_decl, testcase):
	method_names = list(map(lambda m: class_decl.name + '#' + m.name, class_decl.methods))
	return any(testcase.mvn_name.endswith(m_name) for m_name in method_names)


if __name__ == '__main__':
	unittest.main()
