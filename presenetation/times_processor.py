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

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'times_view')
OUTPUT_FILE_NAME = "reps.csv"
RUNNINGS_FILE_NAME = "times.csv"
VALID_TEST_CASES_FILE_NAME = "valid_bugs.csv"


class ReplicationsProcessor(object):
	REP_FIELD_NAME = 'rep'
	PROJ_HEADER = 'project name'
	PROJECT_NAME_FIELD_NAME = 'project name'
	ISSUE_FIELD_NAME = 'issue'
	VALID_FIELD_NAME = 'valid'

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
		complete_issues = self.get_complete_issues(proj, rep_num)
		return sum(map(lambda x: x.time, complete_issues))/len(complete_issues)

	def get_complete_issues(self, proj, rep):
		def get_rep_issues(issues):
			return filter(lambda x: x[ReplicationsProcessor.PROJECT_NAME_FIELD_NAME] == proj + '_' + str(rep), issues)

		return set(
			filter(
				lambda x: self.is_complete_issue(proj, rep, x),
				get_rep_issues(self._runnings)
			)
		)

	def is_complete_issue(self, proj, rep, issue):
		def matchibg_proj_rep(row):
			if ReplicationsProcessor.REP_FIELD_NAME in row.keys():
				return row[ReplicationsProcessor.REP_FIELD_NAME] == rep and \
				       row[ReplicationsProcessor.PROJECT_NAME_FIELD_NAME] == proj
			else:
				return row[ReplicationsProcessor.PROJECT_NAME_FIELD_NAME] == proj + '_' + str(rep)

		def is_confirming(row):
			return matchibg_proj_rep(row) and row[ReplicationsProcessor.ISSUE_FIELD_NAME] == issue and row[
				ReplicationsProcessor.VALID_FIELD_NAME] == 'TRUE'

		return any(
			map(lambda row: is_confirming(row), self._valid_test_cases)
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


if __name__ == '__main__':
	ReplicationsProcessor(sys.argv[1]).process_reps()
