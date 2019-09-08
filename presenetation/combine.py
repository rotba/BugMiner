import csv
import os
import sys
from functools import reduce
from openpyxl import load_workbook
from mvnpy.bug import Bug_data_handler


class Combiner(object):

	def __init__(self, results_dir,
	             combined_path=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'combined')):
		self._projects = map(
			lambda x: Project_Factory.create(x),
			filter(lambda y: is_project_dir(y), os.listdir(results_dir))
		)
		self._combined_path = combined_path

	def combine(self, table_name):
		with open(os.path.join(self._combined_path, table_name), 'a+') as csv_output:
			writer = csv.DictWriter(csv_output, fieldnames=self.infer_fields(table_name), lineterminator='\n')
			writer.writeheader()
			for row in self.reduce_combined_table(table_name):
				writer.writerow(row)

	def reduce_combined_table(self, table_name):
		return reduce(
			lambda acc, curr: acc + curr,
			map(lambda x: x.get_tupples(table_name), self._projects),
			[]
		)


class Project_Factory(object):

	def create(self, path):
		return Project(path)


class Project(object):

	def __init__(self, path):
		def is_table(path):
			return path.ends_with('.csv')

		self._path = path
		self._tables = filter(lambda x: is_table(x), os.listdir(path))

	def get_tupples(self, table_name):
		return self.csv_to_tupples(self.get_table_path(table_name))

	def csv_to_tupples(self, table_file):
		with open(table_file, 'r') as f:
			reader = csv.reader(f)
			return list(reader)

	def get_table_path(self, table_name):
		return reduce(
			lambda acc, curr: curr if acc == None and os.path.basename(curr) == table_name+'.csv' else acc,
			self._tables,
			None
		)


def get_module(path):
	if not path == 'testcase':
		parts = path.split('\\')
		i = 0
		while i < len(parts) - 1:
			if parts[i + 1] == 'src':
				return parts[i]
			i += 1
	return ''


ISSUE_COLUMN = 2
MODULE_COLUMN = 3
COMMIT_COLUMN = 4
TESTCASE_COLUMN = 6
template_path = os.path.join(os.getcwd(), 'static_files\\watch.xlsx')
data_handler = Bug_data_handler(sys.argv[1])
wb = load_workbook(template_path)
valid_bugs_tups = []
invalid_bugs_tups = []
times_tups = []
report_ws = wb["Report"]
valid_bugs_ws = wb["valid_bugs"]
invalid_bugs_ws = wb["invalid_bugs"]
times_ws = wb["times"]
for row in data_handler.get_valid_bugs():
	valid_bugs_ws.append(row)
	valid_bugs_tups.append(row)
for row in data_handler.get_invalid_bugs():
	invalid_bugs_ws.append(row)
	invalid_bugs_tups.append(row)
for row in data_handler.get_times():
	times_ws.append(row)
	times_tups.append(row)
all_issues = []
valid_issues = []
all_commits = []
valid_commits = []
all_module_inspections = []
valid_module_inspections = []
for tup in valid_bugs_tups:
	if not tup[ISSUE_COLUMN] in valid_issues:
		valid_issues.append(tup[ISSUE_COLUMN])
all_issues += valid_issues
for tup in invalid_bugs_tups:
	if not tup[ISSUE_COLUMN] in all_issues:
		all_issues.append(tup[ISSUE_COLUMN])
for tup in valid_bugs_tups:
	if not tup[COMMIT_COLUMN] in valid_commits:
		valid_commits.append(tup[COMMIT_COLUMN])
all_commits += valid_commits
for tup in invalid_bugs_tups:
	if not tup[COMMIT_COLUMN] in all_commits:
		all_commits.append(tup[COMMIT_COLUMN])

for tup in valid_bugs_tups:
	module_inspection_id = tup[ISSUE_COLUMN] + '#' + tup[COMMIT_COLUMN] + '#' + get_module(tup[TESTCASE_COLUMN])
	if not module_inspection_id in valid_module_inspections:
		valid_module_inspections.append(module_inspection_id)
all_module_inspections += valid_module_inspections

for tup in invalid_bugs_tups:
	module_inspection_id = tup[ISSUE_COLUMN] + '#' + tup[COMMIT_COLUMN] + '#' + get_module(tup[TESTCASE_COLUMN])
	if not module_inspection_id in all_module_inspections:
		all_module_inspections.append(module_inspection_id)

tmp = list(set(all_module_inspections) - set(valid_module_inspections))
invalid_module_inspections = list(map(lambda x: x.split('#'), tmp))
invalid_module_inspections.sort()
module_times = list(map(lambda tup: float(tup[3]), times_tups[1:]))
commit_times = {}
for tup in times_tups[1:]:
	if not tup[1] in commit_times.keys():
		commit_times[tup[1]] = float(tup[3])
	else:
		commit_times[tup[1]] += float(tup[3])
issues_times = {}
for tup in times_tups[1:]:
	if not tup[1] in issues_times.keys():
		issues_times[tup[1]] = float(tup[3])
	else:
		issues_times[tup[1]] += float(tup[3])

report_ws['C3'] = '=COUNTIF(valid_bugs!B3:B{},"*Regression*")'.format(3 + len(valid_bugs_tups))
report_ws['C4'] = '=COUNTIF(valid_bugs!B3:B{},"*Delta*")'.format(3 + len(valid_bugs_tups))
report_ws['C5'] = '=COUNTIF(valid_bugs!B3:B{},"*Delta^2*")'.format(3 + len(valid_bugs_tups))
report_ws['C6'] = '=COUNTIF(valid_bugs!B3:B{},"*Delta^3*")'.format(3 + len(valid_bugs_tups))
report_ws['C7'] = '=COUNTIF(valid_bugs!B3:B{},"*Auto-generated*")'.format(3 + len(valid_bugs_tups))
report_ws['C11'] = '=COUNTIFS(invalid_bugs!B3:B{},"*Regression*", invalid_bugs!I3:I{},"*runtime*")'.format(
	3 + len(invalid_bugs_tups), 3 + len(invalid_bugs_tups))
report_ws['C12'] = '=COUNTIFS(invalid_bugs!B3:B{},"*Regression*", invalid_bugs!I3:I{},"*compilation*")'.format(
	3 + len(invalid_bugs_tups), 3 + len(invalid_bugs_tups))
report_ws['C13'] = '=COUNTIFS(invalid_bugs!B3:B{},"*Delta*", invalid_bugs!I3:I{},"*runtime*")'.format(
	3 + len(invalid_bugs_tups), 3 + len(invalid_bugs_tups))
report_ws['C14'] = '=COUNTIFS(invalid_bugs!B3:B{},"*Delta*", invalid_bugs!I3:I{},"*compilation*")'.format(
	3 + len(invalid_bugs_tups), 3 + len(invalid_bugs_tups))
report_ws['C15'] = '=COUNTIFS(invalid_bugs!B3:B{},"*Delta*", invalid_bugs!I3:I{},"*passed*")'.format(
	3 + len(invalid_bugs_tups), 3 + len(invalid_bugs_tups))
report_ws['C16'] = '=COUNTIFS(invalid_bugs!B3:B{},"*Auto-generated*", invalid_bugs!I3:I{},"*runtime*")'.format(
	3 + len(invalid_bugs_tups), 3 + len(invalid_bugs_tups))
report_ws['C17'] = '=COUNTIFS(invalid_bugs!B3:B{},"*Auto-generated*", invalid_bugs!I3:I{},"*compilation*")'.format(
	3 + len(invalid_bugs_tups), 3 + len(invalid_bugs_tups))
report_ws['C18'] = '=COUNTIFS(invalid_bugs!B3:B{},"*Auto-generated*", invalid_bugs!I3:I{},"*passed*")'.format(
	3 + len(invalid_bugs_tups), 3 + len(invalid_bugs_tups))
report_ws['C22'] = float(len(valid_issues)) / float(len(all_issues))
report_ws['C23'] = float(len(valid_commits)) / float(len(all_commits))
report_ws['C24'] = float(len(valid_module_inspections)) / float(len(all_module_inspections))
report_ws['C27'] = float(reduce(lambda x, y: x + y, issues_times.values())) / float(len(issues_times.values()))
report_ws['C28'] = float(reduce(lambda x, y: x + y, commit_times.values())) / float(len(commit_times.values()))
report_ws['C29'] = float(reduce(lambda x, y: x + y, module_times)) / float(len(module_times))
report_ws['C32'] = '=COUNTIF(times!E3:E{},"*[ERROR] COMPILATION ERROR*")/'.format(3 + len(times_tups)) + str(
	len(module_times))
report_ws['C33'] = '=COUNTIF(invalid_bugs!I3:I{},"*No report*")'.format(3 + len(invalid_bugs_tups))
report_ws['C34'] = '=COUNTIF(times!E3:E{},"*Build took too long*")'.format(3 + len(invalid_bugs_tups))
report_ws['C35'] = '=COUNTIF(invalid_bugs!I3:I{},"*Unexpected failure*")'.format(3 + len(invalid_bugs_tups))
report_ws['C38'] = len(all_issues)
report_ws['C39'] = len(all_commits)
report_ws['C40'] = len(all_module_inspections)
wb.save(os.path.join(data_handler.path, 'watch.xlsx'))
