import datetime
import multiprocessing
import os

from .commit_analyzer import IsBugCommitAnalyzer
from git import Repo
# from jira_extractor import JiraExtractor
# from sourceforge_extractor import SourceforgeExtractor
from termcolor import colored
from .utils import get_from_cache

CACHE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cache')


class Extractor(object):
	EARLIEST_BUG = 0

	def __init__(self, repo_dir, inspected_branch):
		self.repo = Repo(repo_dir)
		self.inspected_branch = inspected_branch
		self.manager = multiprocessing.Manager()
		self.cache_dir = os.path.join(CACHE_DIR, os.path.basename(self.repo.working_dir))
		if not os.path.isdir(self.cache_dir):
			os.makedirs(self.cache_dir)

	def extract_possible_bugs_wrapper(self, use_cache, check_trace=False):
		if use_cache:
			return filter(lambda x: self.bugs_filter(x),
			              get_from_cache(os.path.join(self.cache_dir, 'possible_bugs.pkl'),
			                             lambda: self.extract_possible_bugs()))
		else:
			return self.extract_possible_bugs(check_trace=check_trace)

	# Returns tupls of (issue,commit,tests) that may contain bugs
	def extract_possible_bugs(self, **kwargs):
		ans = []
		for hey in self.get_all_commits():

			print(colored('### START HANDLING ###', 'red') + hey.hexsha + ' ' + str(datetime.datetime.now().time()))
			if self.is_bug_fix_commit(hey):
				ans.append(hey)
				print(colored('### APPENDED !###', 'blue'))
			print(colored('### END HANDLING ###', 'green') + hey.hexsha + ' ' + str(datetime.datetime.now().time()))

		x = 1

	# Returns the commits relevant to bug_issue
	def get_issue_commits(self, issue):
		ans = []
		for commit in all_commits:
			if self.is_associated_to_commit(issue, commit):
				ans.append(commit)
		return ans

	# Returns true if the commit message contains the issue key exclusively
	def is_associated_to_commit(self, issue, commit):
		if issue.key in commit.message:
			index_of_char_after_issue_key = commit.message.find(issue.key) + len(issue.key)
			if index_of_char_after_issue_key == len(commit.message):
				return True
			char_after_issue_key = commit.message[commit.message.find(issue.key) + len(issue.key)]
			return not char_after_issue_key.isdigit()
		else:
			return False

	def get_all_commits(self):
		return list(self.repo.iter_commits(self.inspected_branch))

	def get_java_commits(self):
		data = self.repo.git.log('--pretty=format:"sha: %H"', '--name-only').split("sha: ")
		comms = dict(map(lambda d: (d[0], list(filter(lambda x: x.endswith(".java"), d[1:-1]))), list(map(lambda d: d.replace('"', '').replace('\n\n', '\n').split('\n'), data))))
		return dict(map(lambda x: (self.repo.commit(x), comms[x]), list(filter(lambda x: comms[x], comms))))

	# Returns boolean. Filter the bugs to inspect
	def bugs_filter(self, possible_bug):
		if Extractor.EARLIEST_BUG > 0:
			key = possible_bug[0]
			number = int(key.split('-')[1])
			return number >= EARLIEST_BUG
		return True

	def has_parent(self, commit):
		return self.get_parent(commit) is not None

	def get_tests_paths_from_commit(self, commit):
		if not self.has_parent(commit): return []
		return IsBugCommitAnalyzer(commit=commit, parent=self.get_parent(commit),
		                           repo=self.repo).analyze().get_test_paths()

	def get_changed_components(self, commit):
		if not self.has_parent(commit): return []
		return IsBugCommitAnalyzer(commit=commit, parent=self.get_parent(commit),
		                           repo=self.repo).analyze().get_diffed_components()

	def get_parent(self, commit):
		ans = None
		for curr_parent in commit.parents:
			for branch in curr_parent.repo.refs:
				if branch.name == self.inspected_branch:
					ans = curr_parent
					break
		return ans
