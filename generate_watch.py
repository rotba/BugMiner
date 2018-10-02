import os
import sys
from functools import reduce

from openpyxl import load_workbook
from bug.bug import Bug_data_handler
ISSUE_COLUMN = 2
COMMIT_COLUMN = 4
MODULE_COLUMN = 3
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
all_issues+=valid_issues
for tup in invalid_bugs_tups:
    if not tup[ISSUE_COLUMN] in all_issues:
        all_issues.append(tup[ISSUE_COLUMN])
for tup in valid_bugs_tups:
    if not tup[COMMIT_COLUMN] in valid_commits:
        valid_commits.append(tup[COMMIT_COLUMN])
all_commits+=valid_commits
for tup in invalid_bugs_tups:
    if not tup[COMMIT_COLUMN] in all_commits:
        all_commits.append(tup[COMMIT_COLUMN])
for tup in valid_bugs_tups:
    module_inspection_id = tup[ISSUE_COLUMN]+'#'+tup[COMMIT_COLUMN]+'#'+tup[MODULE_COLUMN]
    if not module_inspection_id in valid_module_inspections:
        valid_module_inspections.append(module_inspection_id)
all_module_inspections+=valid_module_inspections
for tup in invalid_bugs_tups:
    module_inspection_id = tup[ISSUE_COLUMN] + '#' + tup[COMMIT_COLUMN] + '#' + tup[MODULE_COLUMN]
    if not module_inspection_id in all_module_inspections:
        all_module_inspections.append(module_inspection_id)

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

report_ws['C15'] = len(valid_issues)/len(all_issues)
report_ws['C16'] = len(valid_commits)/len(all_commits)
report_ws['C17'] = len(valid_module_inspections)/len(all_module_inspections)
report_ws['C20'] = reduce(lambda x, y: x + y, issues_times.values()) / len(issues_times.values())
report_ws['C21'] = reduce(lambda x, y: x + y, commit_times.values()) / len(commit_times.values())
report_ws['C22'] = reduce(lambda x, y: x + y, module_times) / len(module_times)
wb.save(os.path.join(data_handler.path, 'watch.xlsx'))
