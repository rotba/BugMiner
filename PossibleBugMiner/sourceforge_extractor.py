import datetime
import logging
import re

from javadiff.FileDiff import FileDiff
from .commit_analyzer import IsBugCommitAnalyzer
from .extractor import Extractor
from termcolor import colored


class SourceforgeExtractor(Extractor):
	MAX_ISSUES_TO_RETRIEVE = 2000

	# USE_CASH = False

	def __init__(self, repo_dir, branch_inspected):
		super(SourceforgeExtractor, self).__init__(repo_dir, branch_inspected)

	# Returns tupls of (issue,commit,tests) that may contain bugs
	def extract_possible_bugs(self):
		ans = []
		for commit in self.get_all_commits():
			if not self.has_parent(commit): continue
			logging.info(
				colored('### START HANDLING ###', 'red') + commit.hexsha + ' ' + str(datetime.datetime.now().time()))
			analyzer = SourcforgeCommitAnalyzer(commit=commit, parent=self.get_parent(commit), repo=self.repo).analyze()
			if analyzer.is_bug_commit():
				ans.append((analyzer.get_issue(), analyzer.commit.hexsha, analyzer.get_test_paths(), analyzer.get_diffed_components()))
				logging.info(colored('### APPENDED !###', 'blue'))
			logging.info(
				colored('### END HANDLING ###', 'green') + commit.hexsha + ' ' + str(datetime.datetime.now().time()))
		return ans


class SourcforgeCommitAnalyzer(IsBugCommitAnalyzer):

	def __init__(self, commit, parent, repo):
		super(SourcforgeCommitAnalyzer, self).__init__(commit, parent, repo)
		self._bug_number = None

	def analyze(self):
		super(SourcforgeCommitAnalyzer, self).analyze()
		if len(self.commit.parents) == 0: return self
		self._bug_number = self.find_bug_number()
		return self

	def is_bug_commit(self):
		return super(SourcforgeCommitAnalyzer, self).is_bug_commit() and self._bug_number != None

	def get_issue(self):
		return SourcforgeIssue(self._bug_number)

	def find_bug_number(self):
		for diff in self._commit.parents[0].diff(self._commit):
			positive_delta = FileDiff(diff).get_positive_delta()
			return reduce(
				lambda acc, curr: acc if acc != None or self.get_bug_id_from_doc(curr) == None
				else self.get_bug_id_from_doc(curr),
				positive_delta,
				None)

	def get_bug_id_from_doc(self, line):
		match = re.search("bug ([0-9])+", line, re.IGNORECASE)
		if match != None:
			bug_space_id = match.group(0)
			space_id = re.search(" ([0-9])+", bug_space_id).group(0)
			return space_id.strip(' ')


class SourcforgeIssue(object):

	def __init__(self, bug_number):
		self._key = bug_number

	@property
	def key(self):
		return self._key
