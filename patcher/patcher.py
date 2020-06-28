import os
import re
import shutil

import git
import mvnpy
from git_cmd_wrapper import git_cmds_wrapper
from mvnpy import mvn
from patch_files import ChangedFile, ErroredFile, OnlyTestcasesErroredFile

TESTED_PROJECTS_DIR = os.path.join(
	os.path.dirname(os.path.realpath(__file__)), 'tested_projects'
)


class TestcasePatcher(object):
	MAX_CLEANING_ITERATIONS = 2

	def __init__(self, testcases, proj_dir, commit_fix, commit_bug, module_path, generated_tests_diff,
	             gen_commit=None):
		self.testcases = testcases
		self.git_repo = git.Repo(proj_dir)
		self.mvn_repo = mvnpy.Repo.Repo(proj_dir)
		self.commit_fix = self.git_repo.commit(commit_fix)
		self.commit_bug = self.git_repo.commit(commit_bug)
		self.module_path = module_path
		self.generated_tests_diff = generated_tests_diff
		self.gen_commit = self.git_repo.commit(gen_commit) if gen_commit != None else None
		self.proj_dir = os.path.join(TESTED_PROJECTS_DIR, os.path.basename(self.git_repo.working_dir))
		self.files_manager = ProjectFilesManager(self.proj_dir)

	def patch(self):
		self._patch = self.patch_all(self.testcases)
		self.unpatch = self.unpatch_comp_errors(self._patch)
		return self

	def get_patched(self):
		return [x for x in self.get_all_patched() if x not in self.get_all_unpatched()]

	def get_all_patched(self):
		return self._patch.testcases

	def get_all_unpatched(self):
		return reduce(lambda acc, curr: self.get_unpatched(curr) + acc, self.unpatch.errored_files, [])

	def get_unpatched(self, file):
		if isinstance(file, OnlyTestcasesErroredFile):
			return file.testcases
		else:
			return self._patch.get_changed_file(file.path).testcases

	def patch_all(self, testcases):
		patch = Patch()
		for diff in self.get_all_diffs():
			associeted_testcases = self.get_associated_test_case(diff, testcases)
			if not len(associeted_testcases) == 0:
				test_path = self.get_diff_src_path(associeted_testcases, diff)
				target_commit = self.commit_fix if self.gen_commit == None else self.gen_commit
				patch_path = self.generate_patch(commit=target_commit, file=test_path,
				                                 patch_name=os.path.basename(test_path))
				git_cmds_wrapper(
					lambda: self.git_repo.git.execute(['git', 'apply', '--whitespace=nowarn', patch_path])
					, self.git_repo)
				patch.add_changed_file(
					ChangedFile(testcases=associeted_testcases, diff=Diff(patch_path=patch_path), path=test_path)
				)
		return patch

	def unpatch_comp_errors(self, patch):
		unpatch = Unpatch()
		comp_error_report = self.get_compilation_error_report()
		tries = 0
		while self.proj_has_error(comp_error_report) and tries < TestcasePatcher.MAX_CLEANING_ITERATIONS:
			unpatch.add_errored_files(self.clean_errors(comp_error_report, patch))
			tries += 1
			comp_error_report = self.get_compilation_error_report()
		return unpatch

	def get_all_diffs(self):
		regular_diffs = self.commit_fix.diff(self.commit_bug)
		return set(regular_diffs + self.generated_tests_diff)

	def get_associated_test_case(self, diff, testcases):
		ans = []
		for testcase in testcases:
			if self.are_associated_test_paths(diff.a_path, testcase.src_path):
				ans.append(testcase)
		return ans

	def get_diff_src_path(self, associeted_testcases, diff):
		if 'ESTest_scaffolding' in diff.a_path:
			return self.generate_ESTest_scaffolding_path(diff)
		return associeted_testcases[0].src_path

	def generate_ESTest_scaffolding_path(self, diff):
		return os.path.normpath(os.path.join(self.git_repo.working_dir, diff.a_path))

	def are_associated_test_paths(self, path, test_path):
		n_path = os.path.normcase(path)
		n_test_path = os.path.normcase(test_path)
		return n_path in n_test_path or n_path.strip('.evosuite\\best-tests').strip('_scaffolding.java') in n_test_path

	def generate_patch(self, commit, file, patch_name):
		path_to_patch = self.files_manager.patches_dir + '//' + patch_name + '.patch'
		orig_wd = os.getcwd()
		os.chdir(self.git_repo.working_dir)
		if self.commit_bug == None or commit == None:
			cmd = ' '.join(['git', 'diff', 'HEAD', file, '>', path_to_patch])
		else:
			cmd = ' '.join(['git', 'diff', self.commit_bug.hexsha, commit.hexsha, file, '>', path_to_patch])
		os.system(cmd)
		os.chdir(orig_wd)
		return path_to_patch

	def proj_has_error(self, compilation_error_report):
		return len(compilation_error_report) > 0

	def clean_errors(self, compilation_error_report, patch):
		ans = []
		compilation_errors = mvn.get_compilation_errors(compilation_error_report)
		error_files = self.extract_errored_files(compilation_errors)
		for file in error_files:
			if isinstance(file, OnlyTestcasesErroredFile):
				self.clean_testcases(file)
			else:
				self.clean_whole_file(file, patch)
			ans.append(file)
		return ans

	def extract_errored_files(self, compilation_errors):
		ans = []
		files = self.extract_files(compilation_errors)
		for file in files:
			errors = self.extract_file_errors(file, compilation_errors)
			ans.append(ErroredFile.create(file, errors, self.git_repo))
		return ans

	def extract_files(self, compilation_errors):
		return set(map(lambda x: x.path, compilation_errors))

	def extract_file_errors(self, file_path, compilation_errors):
		return filter(lambda x: x.path == file_path, compilation_errors)

	def clean_testcases(self, file):
		self.unpatch_testcases(file.path, file.testcases)

	def clean_whole_file(self, file, patch):
		changed_file = patch.get_changed_file(file.path)
		if changed_file is None:
			git_cmds_wrapper(
				lambda: self.git_repo.git.execute(['git', 'checkout', '--', '-R', file.path]),
				self.git_repo)
			return
		diff = changed_file.diff
		if self.file_is_untracked(file):
			os.remove(file.path)
		else:
			git_cmds_wrapper(lambda: self.git_repo.git.execute(['git', 'apply', '--whitespace=nowarn', '-R', diff.patch_path]), self.git_repo)

	def file_is_untracked(self, file):
		status = self.git_repo.git.status()
		rel_file_path = os.path.relpath(file.path, self.git_repo.working_dir)
		return re.match('[\s\S]*(Untracked files:)[\s\S]*{}'.format(rel_file_path), status) or re.match(
			'[\s\S]*(Untracked files:)[\s\S]*{}'.format(rel_file_path.replace('\\', '/')), status)

	def unpatch_testcases(self, path, testcases):
		positions_to_delete = list(map(lambda t: t.get_lines_range(), testcases))
		with open(path, 'r') as f:
			lines = f.readlines()
		with open(path, 'w') as f:
			i = 1
			for line in lines:
				if any(p[0] <= i <= p[1] for p in positions_to_delete):
					f.write('')
				else:
					f.write(line)
				i += 1

	def get_compilation_error_report(self):
		self.mvn_repo.clean(self.module_path)
		build_report = self.mvn_repo.test_compile(self.module_path)
		return mvn.get_compilation_error_report(build_report)


class Patch(object):

	def __init__(self):
		self._changed_files = []

	@property
	def changed_files(self):
		return self._changed_files

	def add_changed_file(self, changed_file):
		self._changed_files.append(changed_file)

	@property
	def testcases(self):
		return reduce(lambda acc, curr: acc + curr.testcases, self._changed_files, [])

	def get_changed_file(self, path):
		file_sing = filter(lambda x: os.path.normpath(x.path) == os.path.normpath(path), self.changed_files)
		return file_sing[0] if len(file_sing) > 0 else None

	def remove_file(self, path):
		file_sing = filter(lambda x: file_sing.path == path, self.changed_files)
		if len(file_sing) == 0:
			return
		else:
			self._changed_files.remove(file_sing[0])


class Unpatch(object):

	def __init__(self):
		self._errored_files = []

	@property
	def errored_files(self):
		return self._errored_files

	def add_errored_files(self, errored_files):
		self._errored_files += errored_files


class Diff(object):

	def __init__(self, patch_path):
		self._patch_path = patch_path

	@property
	def patch_path(self):
		return self._patch_path


class ProjectFilesManager(object):

	def __init__(self, proj_dir):
		if not os.path.isdir(proj_dir):
			os.makedirs(proj_dir)
		else:
			shutil.rmtree(proj_dir)
			os.makedirs(proj_dir)
		self.proj_dir = proj_dir
		self.patches_dir = os.path.join(proj_dir, 'patches')
		os.makedirs(self.patches_dir)
