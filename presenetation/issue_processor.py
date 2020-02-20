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

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'issue_view')
OUTPUT_FILE_NAME = "issues.csv"
RUNNINGS_FILE_NAME = "times.csv"
VALID_TEST_CASES_FILE_NAME = "valid_bugs.csv"


class IssuesProcessor(object):
	COMPLETE_DESCRIPTION = 'success'
	DESCRIPTION_FIELD_NAME = 'description'
	REP_FIELD_NAME = 'rep'
	ISSUE_HEADER = 'issue'
	PROPER_HEADER = 'proper'
	COMPLETE_HEADER = 'complete'
	PROJECT_NAME_FIELD_NAME = 'project name'
	ISSUE_FIELD_NAME = 'issue'
	VALID_FIELD_NAME = 'valid'
	NOT_PROPER_DESCTIPRIONS = [
		'Compilation failure',
		'Dependencies resolution failure'
		'Failed to execute goal org.codehaus.mojo:animal-sniffer-maven-plugin:1.13:check'
	]

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

	def process(self):
		f_path = os.path.join(self._rep_path, OUTPUT_FILE_NAME)
		reps_amount = self.count_reps()
		with open(f_path, 'a+') as csv_output:
			writer = csv.DictWriter(csv_output, fieldnames=self.infer_fields(reps_amount), lineterminator='\n')
			writer.writeheader()
			for issue in self.get_issues():
				writer.writerow(self.generate_row(issue, reps_amount))

	def generate_row(self, issue, reps_amount):
		ans = {
			IssuesProcessor.ISSUE_HEADER: issue,
			IssuesProcessor.PROPER_HEADER: self.is_proper(issue),
			IssuesProcessor.COMPLETE_HEADER: self.is_complete(issue)
		}
		for rep in range(0, reps_amount, 1):
			ans.update({self.rep_header(rep): self.is_valid(issue, rep)})
		return ans

	def is_valid(self, issue, rep):
		def is_valid_test_case(row):
			return row[IssuesProcessor.PROJECT_NAME_FIELD_NAME].endswith("_" +str(rep)) and \
			       (
					       row[IssuesProcessor.VALID_FIELD_NAME] == 'TRUE' or
					       row[IssuesProcessor.VALID_FIELD_NAME] == 'True'
			       )

		return any(
			map(lambda x: is_valid_test_case(x), self.get_test_cases(issue))
		)

	def is_proper(self, issue):
		def is_proper_running(running):
			return running[IssuesProcessor.DESCRIPTION_FIELD_NAME] in IssuesProcessor.NOT_PROPER_DESCTIPRIONS

		return any(
			map(lambda x: is_proper_running(x), self.get_runnings(issue))
		)

	def is_complete(self, issue):
		def is_complete_running(running):
			return running[IssuesProcessor.DESCRIPTION_FIELD_NAME] == IssuesProcessor.COMPLETE_DESCRIPTION

		return any(
			map(lambda x: is_complete_running(x), self.get_runnings(issue))
		)

	def get_runnings(self, issue):
		return filter(lambda x: x[IssuesProcessor.ISSUE_FIELD_NAME] == issue, self._runnings)

	def get_test_cases(self, issue):
		return filter(lambda x: x[IssuesProcessor.ISSUE_FIELD_NAME] == issue, self._valid_test_cases)

	def infer_fields(self, reps_amount):
		return reduce(
			lambda acc, curr: acc + [self.rep_header(curr)],
			range(0, reps_amount),
			[IssuesProcessor.ISSUE_HEADER, IssuesProcessor.PROPER_HEADER,IssuesProcessor.COMPLETE_HEADER]
		)

	def rep_header(self, rep_num):
		return "valid_" + str(rep_num)

	def count_reps(self):
		def infer_rep_num(row):
			return int(re.findall("[0-9]", row[IssuesProcessor.PROJECT_NAME_FIELD_NAME])[0]) + 1

		return reduce(
			lambda acc, curr: max(acc, infer_rep_num(curr)),
			self._runnings,
			0
		)

	def get_issues(self):
		return set(
			map(lambda x: x[IssuesProcessor.ISSUE_FIELD_NAME], self._runnings)
		)


if __name__ == '__main__':
	IssuesProcessor(sys.argv[1]).process()
