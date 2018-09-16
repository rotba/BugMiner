import pickle
import shutil
import sys
import os
import logging
import mvn_parsers.test_parser as test_parser
import bug.bug as my_bug
import git
import javalang
from git import Repo
from jira import JIRA
from jira import exceptions as jira_exceptions

jira = JIRA(options={'server': 'https://issues.apache.org/jira'})
LOG_FILENAME = 'bugminer_log.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
cache_dir = os.getcwd() + '\\cache'
all_tests = []
all_commits = []
bug_issues = []
branch_inspected = 'master'
repo = None
proj_dir = ''
proj_dir_installed = ''
proj_name = ''
orig_wd = os.getcwd()
patches_dir = ''
MAX_ISSUES_TO_RETRIEVE = 2000
JQL_QUERY = 'project = {} AND issuetype = Bug AND createdDate <= "2018/10/11" ORDER BY  createdDate ASC'


def main(argv):
    bug_data_set = []
    set_up(argv[0])
    possible_bugs = extract_possible_bugs(bug_issues)
    for possible_bug in possible_bugs:
        try:
            bugs = extract_bugs(issue=possible_bug[0], commit=possible_bug[1], tests=possible_bug[2])
            bug_data_set.extend(bugs)
        except my_bug.BugError as e:
            logging.debug(e.msg)
    res = open('results\\' + proj_name, 'w')
    for bug in bug_data_set:
        res.write(str(bug) + '\n')
    # res_file = open('results\\'+proj_name, 'wb')
    # pickle.dump(bug_data_set, res_file)


# Returns bugs solved in the given commit regarding the issue, indicated by the tests
def extract_bugs(issue, commit, tests):
    logging.info("extract_bugs(): working on issue " +issue.key+' in commit '+commit.hexsha)
    ans = []
    invalid_bugs = []
    parent = get_parent(commit)
    if parent == None:
        return ans
    repo.git.checkout(commit)
    commit_testcases = test_parser.get_testcases(tests)
    dict_modules_testcases = divide_to_modules(commit_testcases)
    for module in dict_modules_testcases:
        prepare_project_repo_for_testing(commit, module)
        test_cmd = generate_mvn_test_cmd(tests, module)
        os.system(test_cmd)
        repo.git.reset('--hard')
        prepare_project_repo_for_testing(parent, module)
        commit_new_testcases = get_commit_created_testcases(dict_modules_testcases[module])
        patched_testcases = patch_testcases(dict_modules_testcases[module], commit, parent)
        invalid_bug_testcases = [t for t in commit_new_testcases if not t in patched_testcases ]
        invalid_bugs = list(map(lambda t: my_bug.Bug(issue, commit, t,my_bug.invalid_msg), invalid_bug_testcases))
        ##should be removed in better versions
        invalid_testclasses = list(map(lambda t: t.get_parent, invalid_bug_testcases))
        lost_bug_testcases= [t for t in dict_modules_testcases[module] if not t.get_parent() in invalid_testclasses]
        invalid_bugs += list(map(
            lambda t: my_bug.Bug(issue, commit, t, 'Invalid: testcase is a part of file containing test case that generated compilation error'),lost_bug_testcases))
        for bug in invalid_bugs:
            logging.info('Extracted invalid bug:\n' + str(bug))
        ##should be removed in better versions
        os.system(test_cmd)
        parent_tests = test_parser.get_tests(module)
        parent_testcases = test_parser.get_testcases(parent_tests)
        for testcase in dict_modules_testcases[module]:
            if testcase in parent_testcases:
                parent_testcase = [t for t in parent_testcases if t == testcase][0]
                if testcase.passed() and not parent_testcase.passed():
                    if testcase in commit_new_testcases:
                        bug = my_bug.Bug(issue, commit, testcase, my_bug.created_msg)
                        logging.info('Extracted bug:\n'+str(bug))
                        ans.append(bug)
                    else:
                        bug = my_bug.Bug(issue, commit, testcase, my_bug.regression_msg)
                        logging.info('Extracted bug:\n' + str(bug))
                        ans.append(bug)
    return ans


# Return the diffs the solved the bug in test in commit
def extract_possible_bugs(bug_issues):
    ans = []
    for bug_issue in bug_issues:
        logging.info("extract_possible_bugs(): working on issue " + bug_issue.key)
        issue_tests = []
        #issue_tests += get_tests_from_issue_text(bug_issue)
        issue_commits = get_issue_commits(bug_issue)
        if len(issue_commits) == 0:
            logging.debug('Couldn\'t find commits associated with ' + bug_issue.key)
            continue
        for commit in issue_commits:
            issue_tests += get_tests_from_commit(commit)
            if len(issue_tests) == 0:
                logging.info('Didn\'t associate ' + bug_issue.key + ' with any test')
                continue
            ans.append((bug_issue, commit, issue_tests))
    return ans


# Returns list of testcases that exist in commit_tests and not exist in the current state (commit)
def get_commit_created_testcases(testcases):
    ans = []
    testcases_in_src = []
    for testcase in testcases:
        src_path = testcase.get_src_path()
        if os.path.isfile(src_path):
            with open(src_path, 'r') as src_file:
                tree = javalang.parse.parse(src_file.read())
        else:
            ans.append(testcase)
            continue
        class_decls = [class_dec for _, class_dec in tree.filter(javalang.tree.ClassDeclaration)]
        if not any([testcase_in_class(c,testcase) for c in class_decls]):
            ans.append(testcase)
    return ans


# Returns list of testclases that exist in commit_tests and not exist in the current state (commit)
def get_commit_created_testclasses(commit_tests):
    ans = []
    for test in commit_tests:
        if not os.path.isfile(test.src_path):
            ans.append(test)
    return ans


# Patches tests in the project
def patch_testcases(commit_testcases, commit, prev_commit):
    ans = []
    diff_test_files = []
    dict_diff_testcases = {}
    dict_diff_patch = {}
    set_up_patches_dir()
    for diff in commit.diff(prev_commit):
        associeted_testcases = get_associated_test_case(diff,commit_testcases)
        if not len(associeted_testcases) == 0:
            test_path = associeted_testcases[0].get_src_path()
            patch_path = generate_patch(proj_dir, prev_commit, commit, test_path, os.path.basename(test_path))
            repo.git.execute(['git', 'apply', patch_path])
            dict_diff_testcases[diff] = associeted_testcases
            dict_diff_patch[diff] = patch_path
            ans.extend(associeted_testcases)
    not_compiling_testcases = get_uncompiled_testcases(dict_diff_testcases.values())
    for testcase in not_compiling_testcases:
        diff = [d for d in dict_diff_testcases.keys() if testcase in dict_diff_testcases[d]][0]
        repo.git.execute(['git', 'apply', '-R', dict_diff_patch[diff]])
        ans.remove(testcase)
    return ans


# Creates patch representing the changes occured in file between commit and prev_commit
def generate_patch(git_dir, prev_commit, commit, file, patch_name):
    path_to_patch = patches_dir + '//' + patch_name + '.patch'
    os.chdir(proj_dir)
    cmd = ' '.join(['git', 'diff', prev_commit.hexsha, commit.hexsha, file, '>', path_to_patch])
    os.system(cmd)
    os.chdir(orig_wd)
    return path_to_patch


# returns list of patches that didn't compile from
def get_uncompiled_testcases(testcases_groups):
    ans = []
    for testcases_group in testcases_groups:
        cmd = generate_mvn_test_cmd(testcases_group, testcases_group[0].get_module())
        with os.popen(cmd) as proc:
            build_report = proc.read()
            ans += get_compilation_error_testcases(build_report, testcases_group)
    return ans


# Gets the test case associated with the compilation error
def get_error_test_case(line, testcases):
    ans = None
    path = ''
    error_address = ''
    parts = line.split(' ')
    path_and_error_address = parts[1].split(':')
    error_address = path_and_error_address[len(path_and_error_address) - 1]
    error_line = int(error_address.strip('[]').split(',')[0])
    path = ':'.join(path_and_error_address[:-1])
    if path.startswith('/') or path.startswith('\\'):
        path = path[1:]
    if os.path.isfile(path):
        with open(path, 'r') as java_file:
            tree = javalang.parse.parse(java_file.read())
    else:
        raise FileNotFoundError('in get_error_test_case(), \'path\' not found')
    method = get_compilation_error_method(tree, error_line)
    return [t for t in testcases if method.name == t.get_class_relative_name()][0]


# Checkout to the given commit, cleans the project, and installs the project
def prepare_project_repo_for_testing(parent, module):
    repo.git.add('.')
    try:
        repo.git.commit('-m', 'BugDataMiner run')
    except git.exc.GitCommandError as e:
        if 'nothing to commit, working tree clean' in str(e):
            pass
        else:
            raise e
    repo.git.checkout(parent.hexsha)
    os.system('mvn clean install -DskipTests' + ' -f ' + module)


# Get string array representing possible test names
def get_tests_from_issue_text(input_issue):
    issue = input_issue
    ans = []
    test_names = []
    if hasattr(issue.fields, 'description') and issue.fields.description != None:
        test_names.extend(extract_test_names(issue.fields.description))
    if hasattr(issue.fields, 'attachment'):
        attachments = issue.fields.attachment
        for attachment in attachments:
            test_names.extend(extract_test_names(attachment.filename))
    if hasattr(issue.fields, 'comment'):
        comments = issue.fields.comment
        for comment in comments.comments:
            test_names.extend(extract_test_names(comment.body))

    for test_name in test_names:
        for test in all_tests:
            if test.is_associated(test_name):
                ans.append(test)
                break
    return ans


# Returns the commits relevant to bug_issue
def get_issue_commits(issue):
    ans = []
    for commit in all_commits:
        if is_associated_to_commit(issue, commit):
            ans.append(commit)
    return ans


# Return list of words in text that contains test words
def extract_test_names(text):
    ans = []
    test_words = ['test', 'TEST', 'Test']
    body = text.split(" ")
    for word in body:
        if any(x in word for x in test_words):
            if not word in test_words:  # make sure attachment.filename is not triviale test word
                ans.append(word)
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


# Returns tests that have been changed in the commit
def get_tests_from_commit(commit):
    ans = []
    for file in commit.stats.files.keys():
        if is_test_file(file):
            for test in all_tests:
                if os.path.basename(file).replace('.java', '') in test.get_name():
                    ans.append(test)
    return ans


# Returns mvn command string that runns the given tests in the given module
def generate_mvn_test_cmd(tests, module):
    ans = 'mvn test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -Dtest='
    for test in tests:
        if not ans.endswith('='):
            ans += ','
        ans += test.get_name()
    ans += ' -f ' + module
    return ans


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
    return any(testcase.get_name().endswith(m_name) for m_name in method_names)


# Returns list of strings describing tests or testcases that are not in module dir
def find_test_cases_diff(commit_test_class, src_path):
    ans = []
    testcases_in_src = []
    if os.path.isfile(src_path):
        with open(src_path, 'r') as src_file:
            tree = javalang.parse.parse(src_file.read())
    else:
        return commit_test_class.get_testcases()
    class_decl = [c for c in tree.children[2] if c.name in commit_test_class.get_name()][0]
    for method in class_decl.methods:
        testcases_in_src.append(commit_test_class.get_name() + '#' + method.name)
    for testcase in commit_test_class.get_testcases():
        i = 0
        for testcase_in_src in testcases_in_src:
            if testcase_in_src in testcase.get_name():
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


# Returns the files generated compilation error in the maven build report
def get_compilation_error_testcases(report, testcases):
    ans = []
    report_lines = report.splitlines()
    i=0
    while i < len(report_lines):
        if '[ERROR] COMPILATION ERROR :' in report_lines[i]:
            i+=2
            while not end_of_compilation_errors(report_lines[i]):
                if is_compilation_error_report(report_lines[i]):
                    compilation_error_testcase = get_error_test_case(report_lines[i], testcases)
                    if not compilation_error_testcase in ans:
                        ans.append(compilation_error_testcase)
                i += 1
        else:
            i += 1
    return ans


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
        if are_associated_test_paths(diff.a_path, testcase.get_src_path()):
            ans.append(testcase)
    return ans


# Returns the files generated compilation error in the maven build report
def end_of_compilation_errors(line):
    return '[INFO] -------------------------------------------------------------' in line


# Returns true iff the given report line is a report of compilation error
def is_compilation_error_report(line):
    return line.startswith('[ERROR]')


# Returns the method name of the method containing the compilation error
def get_compilation_error_method(tree, error_line):
    ans = None
    for path, node in tree.filter(javalang.tree.ClassDeclaration):
        for method in node.methods:
            if get_method_line_position(method) < error_line:
                if ans==None:
                    ans =method
                elif get_method_line_position(ans)<get_method_line_position(method):
                    ans = method
    return ans


# Returns the line in which the method starts
def get_method_line_position(method):
    return method.position[0]


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


# Returns the lowest module dir path associated with tests
def get_tests_module_dir(tests):
    ans = proj_dir
    # if not tests[0].get_module()=='':
    if False:
        ans = tests[0].get_module()
    return ans


# Sets up patches dir
def set_up_patches_dir():
    if not os.path.isdir(patches_dir):
        os.makedirs(patches_dir)
    else:
        shutil.rmtree(patches_dir)
        os.makedirs(patches_dir)


def set_up(git_url):
    global all_commits
    global all_tests
    global repo
    global proj_dir
    global proj_dir_installed
    global patches_dir
    global proj_name
    global bug_issues
    global JQL_QUERY
    all_test_cache = cache_dir + '\\all_tests.pkl'
    all_commits_cache = cache_dir + '\\all_commits.pkl'
    bug_issues_cache = cache_dir + '\\bug_issues'
    proj_name = git_url.rsplit('/', 1)[1]
    proj_dir = os.getcwd() + '\\tested_project\\' + proj_name
    proj_dir_installed = proj_dir + '_installed'
    patches_dir = proj_dir + '\\patches'
    try:
        git.Git(os.getcwd() + '\\tested_project').clone(git_url)
    except git.exc.GitCommandError as e:
        logging.debug(e)

    proj_dir = os.getcwd() + '\\tested_project\\' + proj_name
    # os.system('mvn install -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f '+proj_dir)
    if not os.path.isdir(proj_dir_installed):
        shutil.copytree(proj_dir, proj_dir_installed)
    repo = Repo(proj_dir)
    if not os.path.isdir("cache"):
        os.makedirs("cache")
    all_tests = test_parser.get_cached_tests(proj_dir_installed, proj_dir)
    all_commits = list(repo.iter_commits(branch_inspected))
    JQL_QUERY = JQL_QUERY.format(proj_name)
    try:
        bug_issues = jira.search_issues(JQL_QUERY, maxResults=MAX_ISSUES_TO_RETRIEVE)
    except jira_exceptions.JIRAError as e:
        logging.debug(e)


if __name__ == '__main__':
    main(sys.argv[1:]);
