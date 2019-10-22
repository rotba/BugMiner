import csv
import os
import re
import sys
from functools import reduce

maxInt = sys.maxsize

while True:
	# decrease the maxInt value by factor 10
	# as long as the OverflowError occurs.

	try:
		csv.field_size_limit(maxInt)
		break
	except OverflowError:
		maxInt = int(maxInt / 10)

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'issue_running_rep_view')
OUTPUT_FILE_NAME = "reps.csv"
RUNNINGS_FILE_NAME = "times.csv"
VALID_TEST_CASES_FILE_NAME = "valid_bugs.csv"

REP_FIELD_NAME = 'rep'
PROJ_HEADER = 'project name'
PROJECT_NAME_FIELD_NAME = 'project name'
ISSUE_FIELD_NAME = 'issue'
VALID_FIELD_NAME = 'valid'
FIX_COMMIT_FIELD_NAME = 'commit'
MVN_MODULE_FIELD_NAME = 'module'
SUCCESS_FIELD_NAME = 'valid'


class ReplicationsProcessor(object):
	REP_FIELD_NAME = REP_FIELD_NAME
	PROJ_HEADER = PROJ_HEADER
	PROJECT_NAME_FIELD_NAME = PROJECT_NAME_FIELD_NAME
	ISSUE_FIELD_NAME = ISSUE_FIELD_NAME
	VALID_FIELD_NAME = VALID_FIELD_NAME

	def __init__(self, combined_dir, rep_path=DEFAULT_PATH):
		with open(os.path.join(combined_dir, RUNNINGS_FILE_NAME), mode='r') as csv_file:
			csv_reader = csv.DictReader(csv_file)
			self._runnings = reduce(lambda acc, curr: acc + [curr], csv_reader, [])
		with open(os.path.join(combined_dir, VALID_TEST_CASES_FILE_NAME), mode='r') as csv_file:
			csv_reader = csv.DictReader(csv_file)
			self._valid_test_cases = reduce(lambda acc, curr: acc + [curr], csv_reader, [])

		self._rep_path = rep_path
		if not os.path.isdir(self._rep_path):
			os.mkdir(self._rep_path)

	def process_reps(self):
		f_path = os.path.join(self._rep_path, OUTPUT_FILE_NAME)
		reps_amount = self.count_reps()
		projects = self.get_projects()
		with open(f_path, 'a+') as csv_output:
			writer = csv.DictWriter(csv_output, fieldnames=self.infer_fields(reps_amount), lineterminator='\n')
			writer.writeheader()
			for proj in projects:
				writer.writerow(self.generate_row(proj, reps_amount))

	def generate_row(self, proj, reps_amount):
		ans = {ReplicationsProcessor.PROJ_HEADER: proj}
		for rep in range(0, reps_amount, 1):
			ans.update({self.rep_header(rep): self.process_rep(proj, rep)})
		return ans

	def process_rep(self, proj, rep_num):
		return len(
			reduce(
				lambda acc, curr: acc.union(self.get_rep_success_issue_runnings(proj, curr)),
				range(0, rep_num + 1),
				set()
			)
		)

	def get_rep_success_issue_runnings(self, proj, rep):
		return set(
			filter(
				lambda x: self.is_success_issue_running(x) and x.rep == rep and x.project == proj,
				map(lambda y: Running(y), self._runnings)
			)
		)

	def is_success_issue_running(self, running):
		return any(
			map(
				lambda x: x.is_matching_running(running) and x.is_success,
				map(lambda y: TestCase(y), self._valid_test_cases)
			)
		)

	def infer_fields(self, reps_amount):
		return [ReplicationsProcessor.PROJ_HEADER] + reduce(lambda acc, curr: acc + [self.rep_header(curr)],
		                                                    range(0, reps_amount), [])

	def rep_header(self, rep_num):
		return "rep" + str(rep_num)

	def count_reps(self):
		def infer_rep_num(row):
			return int(re.findall("[0-9]", row[ReplicationsProcessor.PROJECT_NAME_FIELD_NAME])[0]) + 1

		return reduce(
			lambda acc, curr: max(acc, infer_rep_num(curr)),
			self._runnings,
			0

		)

	def get_projects(self):
		def infer_project_name(row):
			if re.search("(_[0-9])", row[ReplicationsProcessor.PROJECT_NAME_FIELD_NAME]):
				rep_suffix = re.findall("(_[0-9])", row[ReplicationsProcessor.PROJECT_NAME_FIELD_NAME])[0]
				return row[ReplicationsProcessor.PROJECT_NAME_FIELD_NAME].strip(rep_suffix)
			else:
				return row[ReplicationsProcessor.PROJECT_NAME_FIELD_NAME]

		return reduce(
			lambda acc, curr: acc.union({infer_project_name(curr)}),
			self._runnings,
			set()

		)


class Running(object):
	ISSUE_FIELD_NAME = ISSUE_FIELD_NAME
	FIX_COMMIT_FIELD_NAME = FIX_COMMIT_FIELD_NAME
	MVN_MODULE_FIELD_NAME = MVN_MODULE_FIELD_NAME
	SUCCESS_FIELD_NAME = SUCCESS_FIELD_NAME
	PROJECT_NAME_FIELD_NAME = PROJECT_NAME_FIELD_NAME

	def __init__(self, running):
		self._running = running

	@property
	def issue(self):
		return self._running[Running.ISSUE_FIELD_NAME]

	@property
	def fix_commit(self):
		return self._running[Running.FIX_COMMIT_FIELD_NAME]

	@property
	def mvn_module(self):
		return self._running[Running.MVN_MODULE_FIELD_NAME]

	@property
	def project(self):
		rep_suffix = ''
		if re.search("(_[0-9])", self._running[Running.PROJECT_NAME_FIELD_NAME]):
			rep_suffix = re.findall("(_[0-9])", self._running[Running.PROJECT_NAME_FIELD_NAME])[0]
		return self._running[Running.PROJECT_NAME_FIELD_NAME].strip(rep_suffix)

	@property
	def rep(self):
		return int(re.findall("([0-9])", self._running[Running.PROJECT_NAME_FIELD_NAME])[0])

	def __eq__(self, other):
		if not isinstance(other, Running):
			return NotImplemented
		else:
			return self.issue == other.issue and self.fix_commit == other.fix_commit and self.mvn_module == other.mvn_module


class TestCase(object):
	ISSUE_FIELD_NAME = ISSUE_FIELD_NAME
	FIX_COMMIT_FIELD_NAME = FIX_COMMIT_FIELD_NAME
	MVN_MODULE_FIELD_NAME = MVN_MODULE_FIELD_NAME
	SUCCESS_FIELD_NAME = SUCCESS_FIELD_NAME
	PROJECT_NAME_FIELD_NAME = PROJECT_NAME_FIELD_NAME
	REP_FIELD_NAME = REP_FIELD_NAME

	def __init__(self, row):
		self._row = row

	@property
	def issue(self):
		return self._row[TestCase.ISSUE_FIELD_NAME]

	@property
	def fix_commit(self):
		return self._row[TestCase.FIX_COMMIT_FIELD_NAME]

	@property
	def mvn_module(self):
		return self._row[TestCase.MVN_MODULE_FIELD_NAME]

	@property
	def project(self):
		rep_suffix = ''
		if re.search("(_[0-9])", self._row[TestCase.PROJECT_NAME_FIELD_NAME]):
			rep_suffix = re.findall("(_[0-9])", self._row[TestCase.PROJECT_NAME_FIELD_NAME])[0]
		return self._row[TestCase.PROJECT_NAME_FIELD_NAME].strip(rep_suffix)

	@property
	def rep(self):
		return int(re.findall("([0-9])", self._row[TestCase.PROJECT_NAME_FIELD_NAME])[0])

	@property
	def is_success(self):
		return self._row[TestCase.SUCCESS_FIELD_NAME] == 'TRUE'

	def is_matching_running(self, running):
		return self.issue == running.issue and \
		       self.project == running.project and \
		       self.fix_commit == running.fix_commit and \
		       self.rep == running.rep and \
		       self.mvn_module == running.mvn_module


if __name__ == '__main__':
	ReplicationsProcessor(sys.argv[1]).process_reps()
