import pickle
import shutil
import sys
import os
import logging
import mvn_reports_tests.test_parser as test_parser
import bug.bug as my_bug
from diff.filediff import FileDiff
import git
import javalang
from git import Repo
from jira import JIRA
from jira import exceptions as jira_exceptions


jira = JIRA(options={'server': 'https://issues.apache.org/jira'})
LOG_FILENAME = 'bugminer_log.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
cache_dir = os.getcwd()+'\\cache'
all_tests = []
all_commits = []
bug_issues = []
branch_inspected = 'master'
repo = None
proj_dir = ''
proj_dir_installed = ''
proj_name = ''
MAX_ISSUES_TO_RETRIEVE =2000
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
    res = open('results\\'+proj_name, 'w')
    for bug in bug_data_set:
        res.write(str(bug)+'\n')
    # res_file = open('results\\'+proj_name, 'wb')
    # pickle.dump(bug_data_set, res_file)


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

#Returns tests that had been changed through the commit
def get_tests_from_commit(commit):
    pass

# Returns the commits relevant to bug_issue
def get_issue_commits(issue):
    ans = []
    for commit in all_commits:
        if is_associated_to_commit(issue,commit):
            ans.append(commit)
    return ans


# Returns the commit that solved the bug
def extract_bugs(issue, commit, tests):
    logging.info("extract_bugs(): working on issue " + issue.key)
    ans = []
    invalid_bugs = []
    parent_tests = []
    commit_tests = []
    tests_classes_created_in_commit = []
    testscases_created_in_commit = []
    patched_test_classes = []
    patched_testcases = []
    module_dir = get_tests_module_dir(tests)
    test_cmd = create_mvn_test_cmd(tests, module_dir)
    parent = get_parent(commit)
    if parent == None:
        return ans
    prepare_project_repo_for_testing(commit)
    os.system(test_cmd)
    commit_tests = test_parser.get_tests(project_dir=module_dir)
    repo.git.reset('--hard')
    prepare_project_repo_for_testing(parent)
    tests_classes_created_in_commit = get_commit_created_testcases(commit_tests)
    testscases_created_in_commit = get_commit_created_testclasses(commit_tests)
    #patched_test_classes = patch_test_classes(tests_classes_created_in_commit)
    #patched_testcases = patch_testcases(testcases_created_in_commit)
    for invalid_bug_test_class in list(tests_classes_created_in_commit-patched_test_classes):
        bug = my_bug.Bug(issue, commit, invalid_bug_test_class, 'Invalid: couldn\'t patch test class')
        invalid_bugs.append(bug)
        tests_classes_created_in_commit.remove(invalid_bug_test_class)
    for invalid_bug_testcase in list(testscases_created_in_commit-patched_testcases):
        bug = my_bug.Bug(issue, commit, invalid_bug_testcase, 'Invalid: couldn\'t patch testcase')
        invalid_bugs.append(bug)
        tests_classes_created_in_commit.remove(invalid_bug_test_class)
    os.system(test_cmd)
    parent_tests = test_parser.get_tests(project_dir=module_dir)
    for commit_test in commit_tests:
        parent_test = [t for t in parent_tests if t.__eq__(commit_test)][0]
        if parent_test.passed():
            continue
        if parent_test in patched_test_classes:
            bug = my_bug.Bug(issue, commit, commit_test, 'Created test class')
            ans.append(bug)
            continue
        for commit_testcase in commit_test.get_testcases():
            parent_testcase = [tc for tc in parent_test.get_testcases() if tc.__eq__(commit_testcase)][0]
            if parent_testcase.passed():
                continue
            else:
                if parent_testcase in patched_testcases:
                    bug = my_bug.Bug(issue, commit, commit_testcase, 'Created testcase')
                    ans.append(bug)
                else:
                    bug = my_bug.Bug(issue, commit, commit_testcase, 'Regression testcase')
                    ans.append(bug)

        # if commit_test not in parent_tests:
        #     bug = my_bug.Bug(issue, commit, commit_test, 'Created in commit')
        #     logging.info("extract_bugs(): extracted bug " + str(bug))
        #     ans.append(bug)
        # else:
        #     parent_test = [t for t in parent_tests if t==commit_test][0]
        #     new_created_testcases = list(commit_test.get_testcases()-parent_test.get_testcases())
        #     for new_created_testcase in new_created_testcases:
        #         bug = my_bug.Bug(issue, commit, new_created_testcase, 'New testcase created in commit')
        #         logging.info("extract_bugs(): extracted bug:\n " + str(bug))
        #         ans.append(bug)
        #     if not parent_test.passed():
        #         bug = my_bug.Bug(issue, commit, commit_test, 'Fixed test class in commit')
        #         logging.info("extract_bugs(): extracted bug:\n " + str(bug))
        #         ans.append(bug)
        #     for failed_testcase in parent_test.failed_testcases:
        #         if failed_testcase in commit_test.success_testcases:
        #             bug = my_bug.Bug(issue, commit, commit_test, 'Fixed test case in commit')
        #             logging.info("extract_bugs(): extracted bug:\n " + str(bug))
        #             ans.append(bug)
    return ans

#Return the diffs the solved the bug in test in commit
def extract_possible_bugs(bug_issues):
    ans = []
    for bug_issue in bug_issues:
        logging.info("extract_possible_bugs(): working on issue " + bug_issue.key)
        issue_tests = []
        issue_tests+=get_tests_from_issue_text(bug_issue)
        issue_commits = get_issue_commits(bug_issue)
        if len(issue_commits) ==0:
            logging.debug('Couldn\'t find commits associated with ' + bug_issue.key)
            continue
        for commit in issue_commits:
            issue_tests+=get_tests_from_commit(commit)
            if len(issue_tests) == 0:
                logging.info('Didn\'t associate ' + bug_issue.key + ' with any test')
                continue
            ans.append( (bug_issue, commit, issue_tests ) )
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
    return ans;

#Returns true if file is associated with a test file
def is_test_file(file):
    name = os.path.basename(file.lower())
    if not name.endswith('.java'):
        return False
    if name.endswith('test.java'):
        return True
    if name.startswith('test'):
        return True
    return False

#Returns tests that have been changed in the commit
def get_tests_from_commit(commit):
    ans = []
    for file in commit.stats.files.keys():
        if is_test_file(file):
            for test in all_tests:
                if os.path.basename(file).replace('.java', '') in test.get_name():
                    ans.append(test)
    return ans

#Returns mvn command string that runns the given tests in the given module
def create_mvn_test_cmd(tests, module):
    ans = 'mvn test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -Dtest='
    for test in tests:
        if not ans.endswith('='):
            ans += ','
        ans += test.get_name()
    ans+= '-f '+module
    return ans

#Returns the parent of the given commit in the inspected branch
def get_parent(commit):
    ans = None
    for curr_parent in commit.parents:
        for branch in curr_parent.repo.branches:
            if branch.name == branch_inspected:
                ans = curr_parent
                break
    return ans

#Checkout to the given commit, cleans the project, and installs the project
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

#Returns list of testcases that exist in commit_tests and not exist in the current state (commit)
def get_commit_created_testcases(commit_tests):
    ans = []
    for test in commit_tests:
        ans+=find_test_cases_diff(test, test.src_path)
    return ans

#Returns list of testclases that exist in commit_tests and not exist in the current state (commit)
def get_commit_created_testclasses(commit_tests):
    ans = []
    for test in commit_tests:
        if not os.path.isfile(test.src_path):
            ans.append(test)
    return ans

#Returns list of strings describing tests or testcases that are not in module dir
def find_test_cases_diff(commit_test_class, src_path):
    ans = []
    testcases_in_src = []
    if os.path.isfile(src_path):
        src_file = open(src_path, 'r')
    else:
        return ans
    tree = javalang.parse.parse(src_file.read())
    class_decl = [c for c in tree.children[2] if c.name in commit_test_class.get_name()][0]
    for method in class_decl.methods:
        testcases_in_src.append(commit_test_class.get_name()+'#'+method.name)
    for testcase in commit_test_class.get_testcases():
        i=0
        for testcase_in_src in testcases_in_src:
            if testcase_in_src in testcase.get_name():
                continue
            else:
                i+=1
                if i == len(testcases_in_src):
                    ans.append(testcase)
    return ans


def say_hello():
    logging.info('hey')
    logging.info('brother')

def set_up(git_url):
    global all_commits
    global all_tests
    global repo
    global proj_dir
    global proj_dir_installed
    global proj_name
    global bug_issues
    global JQL_QUERY
    all_test_cache = cache_dir+'\\all_tests.pkl'
    all_commits_cache =  cache_dir+'\\all_commits.pkl'
    bug_issues_cache = cache_dir + '\\bug_issues'
    proj_name = git_url.rsplit('/', 1)[1]
    proj_dir = os.getcwd() + '\\tested_project\\' + proj_name
    proj_dir_installed = proj_dir+'_installed'
    try:
        git.Git(os.getcwd()+ '\\tested_project').clone(git_url)
    except git.exc.GitCommandError as e:
        logging.debug(e)

    proj_dir = os.getcwd() + '\\tested_project\\' + proj_name
    #os.system('mvn install -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -f '+proj_dir)
    if not os.path.isdir(proj_dir_installed):
        shutil.copytree(proj_dir, proj_dir_installed)
    repo = Repo(proj_dir)
    if not  os.path.isdir("cache"):
        os.makedirs("cache")
    all_tests = get_from_cache(all_test_cache,
                               lambda: test_parser.get_tests(proj_dir_installed))
    #all_commits = get_from_cache(all_commits_cache,
    #                           lambda: list(repo.iter_commits(branch_inspected)))
    # bug_issues = get_from_cache(bug_issues_cache,
    #                             lambda: jira.search_issues('project=' + proj_name + ' and type=bug', maxResults=2500))
    all_commits = list(repo.iter_commits(branch_inspected))
    JQL_QUERY = JQL_QUERY.format(proj_name)
    try:
        bug_issues = jira.search_issues(JQL_QUERY, maxResults=MAX_ISSUES_TO_RETRIEVE)
    except jira_exceptions.JIRAError as e:
        logging.debug(e)


#Returns data stored in the cache dir. If not found, retrieves the data using the retrieve func
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

#Returns true if the commit message contains the issue key exclusively
def is_associated_to_commit(issue, commit):
    if issue.key in commit.message:
        char_after_issue_key = commit.message[commit.message.find(issue.key)+len(issue.key)]
        return not char_after_issue_key.isdigit()
    else:
        return False

#Returns the lowest module dir path associated with tests
def get_tests_module_dir(tests):
    ans = proj_dir
    # if not tests[0].get_module()=='':
    if False:
        ans = tests[0].get_module()
    return ans

if __name__ == '__main__':
    main(sys.argv[1:]);


