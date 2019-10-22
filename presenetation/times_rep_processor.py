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

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'times_rep_view')
OUTPUT_FILE_NAME = "reps.csv"
RUNNINGS_FILE_NAME = "times.csv"
VALID_TEST_CASES_FILE_NAME = "valid_bugs.csv"
INVALID_TEST_CASES_FILE_NAME = "invalid_bugs.csv"

REP_FIELD_NAME = 'rep'
PROJ_HEADER = 'project name'
PROJECT_NAME_FIELD_NAME = 'project name'
ISSUE_FIELD_NAME = 'issue'
VALID_FIELD_NAME = 'valid'
FIX_COMMIT_FIELD_NAME = 'commit'
MVN_MODULE_FIELD_NAME = 'module'
SUCCESS_FIELD_NAME = 'valid'
ANIMAL_SNIFFER_CHECK_ERR_DESC = 'Failed to execute goal org.codehaus.mojo:animal-sniffer-maven-plugin:1.13:check'
DEPENDENCY_ERR_DESC = 'Dependencies resolution failure'
DESCRIPTION_FIELD_NAME = 'description'
TIMES_FIELD_NAME = 'time'
COMP_ERR_DESC = 'Compilation failure'


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
		complete_issues = self.get_complete_rep_issues(rep_num, proj)
		return sum(map(lambda x: x.time, complete_issues)) / len(complete_issues)



	def get_rep_filtering_rate(self, rep, proj):
		return float(len(self.get_complete_rep_issues(rep, proj))) / float(len(self.get_rep_test_cases(rep, proj)))

	def get_complete_rep_issues(self, rep, proj):
		def is_complete(running):
			return running.rep == rep and running.project == proj and running.is_complete()

		return filter(
			lambda x: is_complete(x),
			map(lambda y: Running(y),self._runnings)
		)

	def get_rep_test_cases(self, rep, proj):
		return self.get_invalid_test_cases(rep, proj) + self.get_complete_rep_issues(rep, proj)

	def get_invalid_test_cases(self, rep, proj):
		return filter(
			lambda x: x.rep == rep and x.project == proj,
			map(lambda y: TestCase(y), self._invalid_test_cases)
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
	TIMES_FIELD_NAME = TIMES_FIELD_NAME
	ANIMAL_SNIFFER_CHECK_ERR_DESC = ANIMAL_SNIFFER_CHECK_ERR_DESC
	DEPENDENCY_ERR_DESC = DEPENDENCY_ERR_DESC
	DESCRIPTION_FIELD_NAME = DESCRIPTION_FIELD_NAME
	COMP_ERR_DESC = COMP_ERR_DESC
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
	def description(self):
		return self._running[Running.DESCRIPTION_FIELD_NAME]

	@property
	def time(self):
		return float(self._running[Running.TIMES_FIELD_NAME])

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

	def is_complete(self):
		return not any(
			[
				self.description == Running.COMP_ERR_DESC,
				self.description == Running.DEPENDENCY_ERR_DESC,
				self.description == Running.ANIMAL_SNIFFER_CHECK_ERR_DESC
			]
		)

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
