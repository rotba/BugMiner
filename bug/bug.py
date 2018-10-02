import copy
import os
import pickle
import shutil
from enum import Enum
import csv


class Bug(object):
    def __init__(self, issue_key: str, commit_hexsha: str, parent_hexsha: str, fixed_testcase, bugged_testcase, type, valid, desc):
        self._issue_key = issue_key
        self._commit_hexsha = commit_hexsha
        self._parent_hexsha = parent_hexsha
        self._fixed_testcase = fixed_testcase
        self._bugged_testcase = bugged_testcase
        self._module = os.path.basename(bugged_testcase.module)
        self._type = type
        self._desc = desc
        self._valid = valid
        self._has_annotations = 'Test' in list(map(lambda a: a.name, self._bugged_testcase.method.annotations))

    @property
    def issue(self):
        return self._issue_key
    @property
    def commit(self):
        return self._commit_hexsha
    @property
    def parent(self):
        return self._parent_hexsha
    @property
    def bugged_testcase(self):
        return copy.deepcopy(self._bugged_testcase)
    @property
    def fixed_testcase(self):
        return copy.deepcopy(self._bugged_testcase)
    @property
    def desctiption(self):
        return self._desc
    @property
    def type(self):
        return self._type
    @property
    def valid(self):
        return self._valid
    @property
    def has_test_annotation(self):
        return self._has_annotations
    @property
    def module(self):
        return self._module

    def __str__(self):
        return 'type: ' + self.type.value + ' ,issue: ' + self.issue + ' ,commit: ' + self._commit_hexsha+ ' ,parent: ' + self.parent+ ' ,test: ' + self.bugged_testcase.id + ' description: ' + self._desc


class Bug_data_handler(object):
    def __init__(self, path):
        self._path = path
        self._valid_bugs_csv_handler = Bug_csv_report_handler(os.path.join(self._path, 'valid_bugs.csv'))
        self._invalid_bugs_csv_handler = Bug_csv_report_handler(os.path.join(self._path, 'invalid_bugs.csv'))
        self._time_csv_handler = Time_csv_report_handler(os.path.join(self._path, 'times.csv'))

    @property
    def path(self):
        return self._path

    # Adds bug the data
    def add_bug(self, bug):
        if bug.valid:
            self._valid_bugs_csv_handler.add_bug(bug)
        else:
            self._invalid_bugs_csv_handler.add_bug(bug)
        self._store_bug(bug)

    # Adds row to the time tanle
    def add_time(self, issue_key, commit_hexsha, module, time):
        self._time_csv_handler.add_row(issue_key, commit_hexsha, module, time)

    # Stores bug in it's direcrtory
    def _store_bug(self,bug):
        path_to_bug_testclass =self.get_bug_testclass_path(bug)
        if not os.path.exists(path_to_bug_testclass):
            os.makedirs(path_to_bug_testclass)
        bug_path =self.get_bug_path(bug)
        with open(bug_path, 'wb') as bug_file:
            pickle.dump(bug, bug_file)


    # Adds bugs to the csv file
    def add_bugs(self, bugs):
        self._valid_bugs_csv_handler.add_bugs(list(filter(lambda b: b.valid, bugs)))
        self._invalid_bugs_csv_handler.add_bugs(list(filter(lambda b: not b.valid, bugs)))
        for bug in bugs:
            self._store_bug(bug)

    # Attach reports to the testclasses directories
    def attach_reports(self, issue, commit, testcases):
        testclasses = []
        for testcase in testcases:
            if not testcase.parent in testclasses:
                testclasses.append(testcase.parent)
        for testclass in testclasses:
            testclass_path = self.get_testclass_path(issue.key,commit.hexsha, testclass.id)
            report_copy_path = os.path.join(testclass_path, os.path.basename(testclass.get_report_path()))
            shutil.copyfile(testclass.get_report_path(), report_copy_path)


    # Gets the path to the bug's testclass directory
    def get_bug_testclass_path(self, bug):
        return os.path.join(self.path, '/'.join([bug.issue, bug.commit, bug.bugged_testcase.parent.id]))


   # Gets the path to the directory of the testclass in the given commit and issue
    def get_testclass_path(self, issue_key, commit_hexsha, testclass_id):
        return os.path.join(self.path,'/'.join([issue_key,commit_hexsha, testclass_id]))

    # Gets the path to the directory of the testclass in the given commit and issue
    def get_bug_path(self, bug):
        return os.path.join(self.get_bug_testclass_path(bug), bug.bugged_testcase.method.name + '.pickle')

    # Sets up dirctories for bug results
    def set_up_bug_dir(self, issue, commit, testclasses):
        ans = {}
        path_to_bug_dir = os.path.join(self.path, issue.key)
        if not os.path.isdir(path_to_bug_dir):
            os.makedirs(path_to_bug_dir)
        path_to_bug_dir = os.path.join(path_to_bug_dir, commit.hexsha)
        if not os.path.isdir(path_to_bug_dir):
            os.makedirs(path_to_bug_dir)
        for testclass in testclasses:
            path_to_testclass_dir = os.path.join(path_to_bug_dir, testclass.id)
            if not os.path.isdir(path_to_testclass_dir):
                os.makedirs(path_to_testclass_dir)
                ans[testclass.id] = path_to_testclass_dir
        return ans

    # Gets all the data from fb_path
    def fetch_all_data(self, db_path):
        copytree(db_path,self.path)

    def fetch_issue_data(self, db_path, issue):
        copytree(os.path.join(db_path, issue), os.path.join(self.path, issue))

    # Gets all the bugs in issue_key in fixed commit_hexsha
    def get_bugs(self, issue_key, commit_hexsha):
        ans = []
        issue_dir = os.path.join(self.path, issue_key)
        commit_dir = os.path.join(issue_dir, commit_hexsha)
        if not os.path.isdir(commit_dir):
            return ans
        directory = os.fsencode(commit_dir)
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            full_file_path = os.path.join(commit_dir, filename)
            if os.path.isdir(full_file_path):
                ans+= self.get_testclass_bugs(full_file_path)
        return ans

    # Returns all teh bugs in testcalss path
    def get_testclass_bugs(self, testclass_path):
        ans = []
        directory = os.fsencode(testclass_path)
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            if filename.endswith(".pickle"):
                full_path = os.path.join(testclass_path, filename)
                with open(full_path, 'rb') as bug_file:
                    ans.append(pickle.load(bug_file))
        return ans

    # Gets the patch applying bug
    def get_patch(self, bug):
        testclass_path = self.get_testclass_path(bug.issue, bug.commit, bug.bugged_testcase.parent.id)
        directory = os.fsencode(testclass_path)
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            if filename.endswith(".patch"):
                return os.path.join(testclass_path, filename)

    # Gets valid_bugs_tuiplles
    def get_valid_bugs(self):
        ans = []
        with open(self._valid_bugs_csv_handler.path, 'r') as f:
            reader = csv.reader(f)
            ans = list(reader)
        return ans

    # Gets invalid_bugs_tuiplles
    def get_invalid_bugs(self):
        ans = []
        with open(self._invalid_bugs_csv_handler.path, 'r') as f:
            reader = csv.reader(f)
            ans = list(reader)
        return ans

    # Gets invalid_bugs_tuiplles
    def get_times(self):
        ans = []
        with open(self._time_csv_handler.path, 'r') as f:
            reader = csv.reader(f)
            ans = list(reader)
        return ans



class Bug_csv_report_handler(object):
    def __init__(self, path):
        self._writer = None
        self._path = path
        self._fieldnames = ['valid','type','issue','module','commit','parent', 'testcase', 'has_test_annotation','description']
        if not os.path.exists(path):
            with open(self._path, 'w+', newline='') as csv_output:
                writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames)
                writer.writeheader()
     #Adds bug to the csv file
    def add_bug(self, bug):
        with open(self._path, 'a', newline='') as csv_output:
            writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames)
            writer.writerow(self.generate_csv_tupple(bug))

    # Adds bugs to the csv file
    def add_bugs(self, bugs):
        with open(self._path, 'a', newline='') as csv_output:
            writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames)
            for bug in bugs:
                writer.writerow(self.generate_csv_tupple(bug))

    # Generated csv bug tupple
    def generate_csv_tupple(self, bug):
        return {'valid': bug.valid,
                'type': bug.type.value,
                'issue': bug.issue,
                'module': bug.module,
                'commit': bug.commit,
                'parent': bug.parent,
                'testcase': bug.bugged_testcase.mvn_name,
                'has_test_annotation': bug.has_test_annotation,
                'description': bug.desctiption}

    @property
    def path(self):
        return self._path

class Time_csv_report_handler(object):
    def __init__(self, path):
        self._writer = None
        self._path = path
        self._fieldnames = ['issue', 'commit','module', 'time']
        if not os.path.exists(path):
            with open(self._path, 'w+', newline='') as csv_output:
                writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames)
                writer.writeheader()
     #Adds bug to the csv file
    def add_row(self, issue_key, commit_hexsha, module, time):
        with open(self._path, 'a', newline='') as csv_output:
            writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames)
            writer.writerow(self.generate_csv_tupple(issue_key, commit_hexsha, module, time))


    # Generated csv bug tupple
    def generate_csv_tupple(self, issue_key, commit_hexsha, module, time):
        return {'issue': issue_key,
                'commit': commit_hexsha,
                'module': module,
                'time': time}

    @property
    def path(self):
        return self._path

class BugError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


invalid_comp_error_desc = 'testcase genrated compilation error when patched'
invalid_rt_error_desc = 'testcase genrated runtime error when tested'
invalid_passed_desc = 'testcase passed in parent'
invalid_not_fixed_failed_desc = 'testcase failed in commit'
invalid_not_fixed__error_desc = 'testcase generated runtime error in commit'

class Bug_type(Enum):
    DELTA = "Delta"
    REGRESSION = "Regression"
    def __str__(self):
        return self.value
    def __repr__(self):
        return self.value


def create_bug(issue, commit, parent, testcase, parent_testcase, type) -> Bug:
    if testcase.passed and parent_testcase.failed:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase,bugged_testcase=parent_testcase, type=type, valid=True,desc='')
    elif testcase.passed and parent_testcase.has_error:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase, bugged_testcase=parent_testcase,
                   type=type,valid=False,desc=invalid_rt_error_desc + ' ' + parent_testcase.get_error())
    elif testcase.passed and parent_testcase.passed:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase, bugged_testcase=parent_testcase,
                   type=type,valid=False, desc=invalid_passed_desc)
    elif testcase.failed:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase, bugged_testcase=parent_testcase,
                   type=type,valid=False, desc=invalid_not_fixed_failed_desc)
    elif testcase.has_error:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase, bugged_testcase=parent_testcase,
                   type=type,valid=False,desc=invalid_not_fixed__error_desc+' '+testcase.get_error())
    else:
        assert 0==1

# copy directory from stackoverflow
def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s) and not os.path.isdir(d):
            shutil.copytree(s, d, symlinks, ignore)
        elif os.path.isfile(s) and not os.path.isfile(d):
            shutil.copy2(s, d)