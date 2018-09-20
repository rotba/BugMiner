import pickle
import shutil
import sys
import os
import logging
import time
import mvn_parsers.test_parser as test_parser
import bug.bug as my_bug
import git
import javalang
from git import Repo
from jira import JIRA
from jira import exceptions as jira_exceptions

jira = JIRA(options={'server': 'https://issues.apache.org/jira'})
all_commits = []
bug_issues = []
branch_inspected = 'master'
repo = None
proj_dir = ''
proj_name = ''
orig_wd = os.getcwd()
patches_dir = ''
proj_results_dir = ''
cache_dir = ''
valid_bugs_csv_path= ''
invalid_bugs_csv_path = ''
dict_key_issue = {}
MAX_ISSUES_TO_RETRIEVE = 2000
JQL_QUERY = 'project = {} AND issuetype = Bug AND createdDate <= "2018/10/11" ORDER BY  createdDate ASC'


def main(argv):
    bug_data_set = []
    set_up(argv[0])
    valid_bugs_csv_handler = my_bug.Bug_csv_report_handler(valid_bugs_csv_path)
    invalid_bugs_csv_handler = my_bug.Bug_csv_report_handler(invalid_bugs_csv_path)
    possible_bugs =get_from_cache(os.path.join(cache_dir, 'possible_bugs.pkl'), lambda :extract_possible_bugs(bug_issues))
    #possible_bugs =extract_possible_bugs(bug_issues)
    for possible_bug in possible_bugs:
        valid_and_invalid_bugs = extract_bugs(issue=dict_key_issue[possible_bug[0]], commit=repo.commit(possible_bug[1]), tests_paths=possible_bug[2])
        bug_data_set.extend(valid_and_invalid_bugs[0])
        valid_bugs_csv_handler.add_bugs(valid_and_invalid_bugs[0])
        invalid_bugs_csv_handler.add_bugs(valid_and_invalid_bugs[1])
    # res = open('results\\' + proj_name, 'w')
    # for bug in bug_data_set:
    #     res.write(str(bug) + '\n')
    # res_file = open('results\\'+proj_name, 'wb')
    # pickle.dump(bug_data_set, res_file)


# Returns bugs solved in the given commit regarding the issue, indicated by the tests
def extract_bugs(issue, commit, tests_paths):
    logging.info("extract_bugs(): working on issue " + issue.key+' in commit ' + commit.hexsha)
    valid_bugs = []
    invalid_bugs = []
    parent = get_parent(commit)
    if parent == None:
        return (valid_bugs, invalid_bugs)
    git_cmds_wrapper(lambda: repo.git.reset('--hard'))
    git_cmds_wrapper(lambda: repo.git.checkout(commit.hexsha))
    commit_tests_object = list(map(lambda t_path: test_parser.TestClass(t_path),tests_paths))
    commit_testcases = test_parser.get_testcases(commit_tests_object)
    dict_modules_testcases = divide_to_modules(commit_testcases)
    for module in dict_modules_testcases:
        commit_valid_testcases = []
        prepare_project_repo_for_testing(commit, module)
        test_cmd = test_parser.generate_mvn_test_cmd(dict_modules_testcases[module], module)
        os.system(test_cmd)
        commit_valid_testcases = attach_reports(dict_modules_testcases[module], issue, commit, invalid_bugs)
        git_cmds_wrapper(lambda: repo.git.reset('--hard'))
        prepare_project_repo_for_testing(parent, module)
        delta_testcases = get_delta_testcases(commit_valid_testcases)
        patched_testcases = patch_testcases(commit_valid_testcases, commit, parent)
        invalid_bug_testcases = [t for t in delta_testcases if not t in patched_testcases]
        invalid_bugs += list(map(lambda t: my_bug.Bug(issue, commit, t, my_bug.invalid_msg), invalid_bug_testcases))
        ##should be removed in better versions
        invalid_testclasses = list(map(lambda t: t.get_parent, invalid_bug_testcases))
        lost_bug_testcases = [t for t in dict_modules_testcases[module] if not t.get_parent() in invalid_testclasses]
        invalid_bugs += list(map(lambda t: my_bug.Bug(issue, commit, t,'Invalid, testcase is a part of file containing test case that generated compilation error'),lost_bug_testcases))
        ##should be removed in better versions
        os.system(test_cmd)
        parent_valid_testcases = []
        parent_tests = test_parser.get_tests(module)
        all_parent_testcases = test_parser.get_testcases(parent_tests)
        relevant_parent_testcases = list(filter(lambda t: t in commit_valid_testcases,all_parent_testcases))
        parent_valid_testcases = attach_reports(relevant_parent_testcases, issue, commit, invalid_bugs)
        for testcase in commit_valid_testcases:
            if testcase in parent_valid_testcases:
                parent_testcase = [t for t in parent_valid_testcases if t == testcase][0]
                if testcase.passed() and not parent_testcase.passed():
                    if testcase in delta_testcases:
                        bug = my_bug.Bug(issue, commit, testcase, my_bug.created_msg)
                        valid_bugs.append(bug)
                    else:
                        bug = my_bug.Bug(issue, commit, testcase, my_bug.regression_msg)
                        valid_bugs.append(bug)
        git_cmds_wrapper(lambda: repo.git.reset('--hard'))
        git_cmds_wrapper(lambda: repo.git.clean('-xdf'))

        return (valid_bugs, invalid_bugs)

# Attaches reports to testcases and returns the testcases that reports were successfully attached to them.
# Handles exceptions, updates invalid_bugs
def attach_reports(testcases, issue, commit, invalid_bugs):
    ans = []
    for testcase in testcases:
        if testcase.get_parent().get_report() is None:
            try:
                attach_report(testcase)
                ans.append(testcase)
            except test_parser.TestParserException as e:
                invalid_bug = my_bug.Bug(issue, commit, testcase, 'Invalid, '+str(e))
                invalid_bugs.append(invalid_bug)
            except my_bug.BugError as e:
                invalid_bug = my_bug.Bug(issue, commit, testcase, 'Invalid, '+str(e))
                invalid_bugs.append(invalid_bug)
        else:
            ans.append(testcase)
    return ans


# Returns tupls of (issue,commit,tests) that may contain bugs
def extract_possible_bugs(bug_issues):
    ans = []
    for bug_issue in bug_issues:
        logging.info("extract_possible_bugs(): working on issue " + bug_issue.key)
        issue_commits = get_issue_commits(bug_issue)
        if len(issue_commits) == 0:
            logging.debug('Couldn\'t find commits associated with ' + bug_issue.key)
            continue
        for commit in issue_commits:
            issue_tests = get_tests_paths_from_commit(commit)
            if len(issue_tests) == 0:
                logging.info('Didn\'t associate ' + bug_issue.key + ' with any test')
                continue
            ans.append((bug_issue.key, commit.hexsha, issue_tests))
    return ans


# Returns tests that have been changed in the commit in the current state of the project
def get_tests_paths_from_commit(commit):
    ans = []
    diff_index = commit.parents[0].diff(commit)
    for file in commit.stats.files.keys():
        if is_test_file(file):
            try:
                diff = list(filter(lambda d: d.a_path == file, diff_index))[0]
            except IndexError as e:
                logging.info('No diff for '+file+' in commit '+commit.hexsha)
                return ans
            if not diff.deleted_file:
                ans.append(os.path.join(repo.working_dir, file))
    return ans


# Returns list of testcases that exist in commit_tests and not exist in the current state (commit)
def get_delta_testcases(testcases):
    ans = []
    for testcase in testcases:
        src_path = testcase.get_path()
        if os.path.isfile(src_path):
            with open(src_path, 'r') as src_file:
                tree = javalang.parse.parse(src_file.read())
        else:
            ans.append(testcase)
            continue
        class_decls = [class_dec for _, class_dec in tree.filter(javalang.tree.ClassDeclaration)]
        if not any([testcase_in_class(c, testcase) for c in class_decls]):
            ans.append(testcase)
    return ans


# Patches tests in the project
def patch_testcases(commit_testcases, commit, prev_commit):
    ans = []
    dict_diff_testcases = {}
    dict_diff_patch = {}
    set_up_patches_dir()
    for diff in commit.diff(prev_commit):
        associeted_testcases = get_associated_test_case(diff, commit_testcases)
        if not len(associeted_testcases) == 0:
            test_path = associeted_testcases[0].get_path()
            patch_path = generate_patch(proj_dir, prev_commit, commit, test_path, os.path.basename(test_path))
            git_cmds_wrapper(lambda :repo.git.execute(['git', 'apply', patch_path]))
            dict_diff_testcases[diff] = associeted_testcases
            dict_diff_patch[diff] = patch_path
            ans.extend(associeted_testcases)
    not_compiling_testcases = get_uncompiled_testcases(list(dict_diff_testcases.values()))
    for testcase in not_compiling_testcases:
        diff = [d for d in dict_diff_testcases.keys() if testcase in dict_diff_testcases[d]][0]
        git_cmds_wrapper(lambda: repo.git.execute(['git', 'apply', '-R', dict_diff_patch[diff]]))
        ans.remove(testcase)
    return ans


# Creates patch representing the changes occured in file between commit and prev_commit
def generate_patch(git_dir, prev_commit, commit, file, patch_name):
    path_to_patch = patches_dir + '//' + patch_name + '.patch'
    os.chdir(git_dir)
    cmd = ' '.join(['git', 'diff', prev_commit.hexsha, commit.hexsha, file, '>', path_to_patch])
    os.system(cmd)
    os.chdir(orig_wd)
    return path_to_patch

# Checkout to the given commit, cleans the project, and installs the project
def prepare_project_repo_for_testing(parent, module):
    repo.git.add('.')
    git_cmds_wrapper(lambda: repo.git.commit('-m', 'BugDataMiner run'))
    git_cmds_wrapper(lambda: repo.git.checkout(parent.hexsha))
    os.system('mvn clean install -DskipTests' + ' -f ' + module)


# returns list of patches that didn't compile from
def get_uncompiled_testcases(testcases_groups):
    ans = []
    for testcases_group in testcases_groups:
        clean_cmd = test_parser.generate_mvn_clean_cmd(testcases_group[0].get_module())
        os.system(clean_cmd)
        test_compile_cmd = test_parser.generate_mvn_test_compile_cmd(testcases_group[0].get_module())
        with os.popen(test_compile_cmd) as proc:
            build_report = proc.read()
            ans += test_parser.get_compilation_error_testcases(build_report, testcases_group)
    return ans


# attaches reports to all the test claases  of all the testscases. handles
def attach_report(testcase):
    test_class = testcase.get_parent()
    if not os.path.isfile(test_class.get_report_path()):
        raise my_bug.BugError('Unexpected: No report for '+str(test_class))
    test_class.set_report(test_parser.TestClassReport(test_class.get_report_path(), test_class.get_module()))


# Returns the commits relevant to bug_issue
def get_issue_commits(issue):
    ans = []
    for commit in all_commits:
        if is_associated_to_commit(issue, commit):
            ans.append(commit)
    return ans


# Returns true if file is associated with a test file
def is_test_file(file):
    name = os.path.basename(file.lower())
    if not name.endswith('.java'):
        return False
    if name.endswith('test.java'):
        return True
    if name.startswith('test'):
        return True
    return False


# Returns the parent of the given commit in the inspected branch
def get_parent(commit):
    ans = None
    for curr_parent in commit.parents:
        for branch in curr_parent.repo.branches:
            if branch.name == branch_inspected:
                ans = curr_parent
                break
    return ans


# Returns true if testcase is in class_decl
def testcase_in_class(class_decl, testcase):
    method_names = list(map(lambda m: class_decl.name + '#' + m.name, class_decl.methods))
    return any(testcase.get_mvn_name().endswith(m_name) for m_name in method_names)


# Returns list of strings describing tests or testcases that are not in module dir
def find_test_cases_diff(commit_test_class, src_path):
    ans = []
    testcases_in_src = []
    if os.path.isfile(src_path):
        with open(src_path, 'r') as src_file:
            tree = javalang.parse.parse(src_file.read())
    else:
        return commit_test_class.get_testcases()
    class_decl = [c for c in tree.children[2] if c.name in commit_test_class.get_mvn_name()][0]
    for method in class_decl.methods:
        testcases_in_src.append(commit_test_class.get_mvn_name() + '#' + method.name)
    for testcase in commit_test_class.get_testcases():
        i = 0
        for testcase_in_src in testcases_in_src:
            if testcase_in_src in testcase.get_mvn_name():
                continue
            else:
                i += 1
                if i == len(testcases_in_src):
                    ans.append(testcase)
    return ans


# Returns true if the two paths are associated to the same thest
def are_associated_test_paths(path, test_path):
    n_path = os.path.normcase(path)
    n_test_path = os.path.normcase(test_path)
    return n_path in n_test_path


# Returns dictionary containing pairs of module and it's associated testcases
def divide_to_modules(tests):
    ans = {}
    for test in tests:
        if not test.get_module() in ans.keys():
            ans[test.get_module()] = []
        ans[test.get_module()].append(test)
    return ans


# Returns list of all the diffs associated with test case
def get_associated_test_case(diff, testcases):
    ans = []
    for testcase in testcases:
        if are_associated_test_paths(diff.a_path, testcase.get_path()):
            ans.append(testcase)
    return ans



# Returns data stored in the cache dir. If not found, retrieves the data using the retrieve func
def get_from_cache(cache_file_path, retrieve_func):
    if os.path.isfile(cache_file_path):
        cache_file = open(cache_file_path, 'rb')
        ans = pickle.load(cache_file)
        cache_file.close()
        return ans
    else:
        data = retrieve_func()
        cache_file = open(cache_file_path, 'wb')
        pickle.dump(data, cache_file)
        cache_file.close()
        return data


# Returns true if the commit message contains the issue key exclusively
def is_associated_to_commit(issue, commit):
    if issue.key in commit.message:
        char_after_issue_key = commit.message[commit.message.find(issue.key) + len(issue.key)]
        return not char_after_issue_key.isdigit()
    else:
        return False


# Sets up patches dir
def set_up_patches_dir():
    if not os.path.isdir(patches_dir):
        os.makedirs(patches_dir)
    else:
        shutil.rmtree(patches_dir)
        os.makedirs(patches_dir)

#Wraps git command. Handles excpetions mainly
def git_cmds_wrapper(git_cmd):
    try:
        git_cmd()
    except git.exc.GitCommandError as e:
        if 'Another git process seems to be running in this repository, e.g.' in str(e):
            logging.info(str(e))
            time.sleep(2)
            git_cmds_wrapper(lambda : git_cmd())
        elif 'nothing to commit, working tree clean' in str(e):
            pass
        elif 'Please move or remove them before you switch branches.' in str(e):
            logging.info(str(e))
            git_cmds_wrapper(lambda: repo.git.reset('--hard'))
            git_cmds_wrapper(lambda: repo.git.clean('-xdf'))
            time.sleep(2)
            git_cmds_wrapper(lambda: git_cmd())
        elif 'already exists and is not an empty directory.' in str(e):
            pass
        else:
            raise e

def set_up(git_url):
    global all_commits
    global bug_issues
    global dict_key_issue
    global dict_hash_commit
    global repo
    global proj_dir
    global patches_dir
    global proj_results_dir
    global proj_name
    global JQL_QUERY
    global valid_bugs_csv_path
    global invalid_bugs_csv_path
    global cache_dir
    cache_dir = os.getcwd() + '\\cache'
    proj_name = git_url.rsplit('/', 1)[1]
    proj_dir = os.getcwd() + '\\tested_project\\' + proj_name
    patches_dir = proj_dir + '\\patches'
    results_dir = os.path.join(os.getcwd(), 'results')
    proj_results_dir = os.path.join(results_dir, proj_name)
    valid_bugs_csv_path = os.path.join(proj_results_dir, 'bug_table.csv')
    invalid_bugs_csv_path = os.path.join(proj_results_dir, 'invalid_bugs.csv')
    if os.path.isfile(valid_bugs_csv_path):
        raise Exception('The csv results of an old BugMiner running is in the project results dir ('+proj_results_dir+')\n please save it in a different directory before running BugMiner')
    if os.path.isfile(invalid_bugs_csv_path):
        raise Exception('The csv results of an old BugMiner running is in the project results dir ('+proj_results_dir+')\n please save it in a different directory before running BugMiner')
    git_cmds_wrapper(lambda: git.Git(os.getcwd() + '\\tested_project').clone(git_url))
    proj_dir = os.getcwd() + '\\tested_project\\' + proj_name
    if not os.path.isdir(proj_results_dir):
        os.makedirs(proj_results_dir)
    LOG_FILENAME = os.path.join(proj_results_dir, 'log.log')
    logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
    repo = Repo(proj_dir)
    if not os.path.isdir("cache"):
        os.makedirs("cache")
    all_commits = list(repo.iter_commits(branch_inspected))
    JQL_QUERY = JQL_QUERY.format(proj_name)
    try:
        bug_issues = jira.search_issues(JQL_QUERY, maxResults=MAX_ISSUES_TO_RETRIEVE)
    except jira_exceptions.JIRAError as e:
        logging.debug(e)
    for issue in bug_issues:
        dict_key_issue[issue.key] = issue


if __name__ == '__main__':
    main(sys.argv[1:]);
