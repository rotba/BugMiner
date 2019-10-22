import csv
import os
import sys
from functools import reduce

from PossibleBugMiner.extractor_factory import ExtractorFactory

maxInt = sys.maxsize

while True:
	# decrease the maxInt value by factor 10
	# as long as the OverflowError occurs.

	try:
		csv.field_size_limit(maxInt)
		break
	except OverflowError:
		maxInt = int(maxInt / 10)

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'candidates')
USE_CACHE = False


class CandidatedPresentor(object):
	PROJ_HEADER = 'project name'
	ISSUE_COL = 'issue'
	FIX_COMMIT_COL = 'fix-commit'
	TESTS_COL = 'tests_ignore_ignore'

	def __init__(self, git_dir, issue_tracker_url, specific_issue = None, jql_query=None, branch_insptected = 'origin/master',candidates_path=DEFAULT_PATH):

		self._git_dir = git_dir
		self._branch_inspected = branch_insptected
		self._issue_tracker_url = issue_tracker_url
		self._speceific_issue = specific_issue
		self._jql_query = jql_query
		self._candidates_path = os.path.join(candidates_path, os.path.basename(self._git_dir))
		if not os.path.isdir(self._candidates_path):
			os.mkdir(self._candidates_path)

	def present(self):
		candidates = ExtractorFactory.create(
			repo_dir=self._git_dir, branch_inspected=self._branch_inspected, issue_tracker_url=self._issue_tracker_url,
			issue_key=self._speceific_issue, query=self._jql_query
		).extract_possible_bugs_wrapper(use_cache=USE_CACHE)
		f_path =os.path.join(self._candidates_path, 'candidates.csv')
		if os.path.isfile(f_path):
			os.remove(f_path)
		with open(f_path, 'a+') as csv_output:
			writer = csv.DictWriter(csv_output, fieldnames=self.infer_fields(), lineterminator='\n')
			writer.writeheader()
			for row in map(lambda x: self.candidate_to_row(x), candidates):
				writer.writerow(row)

	def candidate_to_row(self, candidate):
		return {
			CandidatedPresentor.ISSUE_COL: candidate.issue,
			CandidatedPresentor.FIX_COMMIT_COL: candidate.fix_commit,
			CandidatedPresentor.TESTS_COL: candidate.tests
		}

	def reduce_combined_table(self, table_name):
		return reduce(
			lambda acc, curr: acc + curr,
			map(lambda x: map(lambda y: self.wrap_project_row(y, x), x.get_rows(table_name)), self._projects),
			[]
		)

	def infer_fields(self):
		return [
			CandidatedPresentor.ISSUE_COL,
			CandidatedPresentor.FIX_COMMIT_COL,
			CandidatedPresentor.TESTS_COL
		]


class Project_Factory(object):

	@classmethod
	def create(self, path):
		return Project(path)


class Project(object):

	def __init__(self, path):
		def is_table(path):
			return path.endswith('.csv')

		self._path = path
		self._data_path = os.path.join(self._path, 'data')
		self._name = os.path.basename(path)
		self._tables = filter(lambda x: is_table(x),
		                      map(lambda y: os.path.join(self._data_path, y), os.listdir(self._data_path)))

	@property
	def name(self):
		return self._name

	def get_rows(self, table_name):
		return self.csv_to_rows(self.get_table_path(table_name))

	def csv_to_rows(self, table_file):
		with open(table_file, 'r') as f:
			reader = csv.DictReader(f)
			return list(reader)

	def get_table_path(self, table_name):
		return reduce(
			lambda acc, curr: curr if acc == None and os.path.basename(curr) == table_name + '.csv' else acc,
			self._tables,
			None
		)

	def get_headers(self, table_name):
		with open(self.get_table_path(table_name), "rb") as f:
			reader = csv.reader(f)
			return reader.next()


if __name__ == '__main__':
	CandidatedPresentor(
		*reduce(lambda acc, curr: acc + (curr,) if not curr is None else acc, sys.argv[1:], tuple())
	).present()
