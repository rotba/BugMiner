import pickle
import sys
import os
import csv
import logging
import test_parser
import bug
import git
from git import Repo
from jira import JIRA


jira = JIRA(options={'server': 'https://issues.apache.org/jira'})
LOG_FILENAME = 'bug_create.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
cache_dir = os.getcwd()+'\\cache'
all_tests = []
all_commits = []
bug_issues = []
branch_inspected = 'master'
repo = None
git_dir = ''
proj_name = ''
MAX_ISSUES_TO_RETRIEVE =200


def main(argv):
    bug_data_set = []
    set_up(argv[0])
    for bug_issue in bug_issues:
        try:
            issue_tests = get_issue_tests(bug_issue)
            issue_commits = get_issue_commits(bug_issue)
            fixes = get_fixes(issue_commits, issue_tests)
            diffs = get_diffs(commit, test)
            # bug = Bug(bug_issue, commit, test, diffs)
        except bug.BugError as e:
            logging.debug(e.msg)

    # commits = extract_critical_commits(repo)
    # with open("output.csv", "a") as output:
    #     wr = csv.writer(output, dialect='excel')
    #     wr.writerow(['commis\\tests'] + all_tests)
    # for commit in commits:
    #     if 'TIKA-2673' in commit.message:
    #         tests_fixed_in_commit = get_tests_fixed_in_commit(commit, all_tests)


# Get string array representing possible test names
def get_issue_tests(issue):
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
    if len(ans) == 0:
        raise bug.BugError('Could not find tests associated with ' + issue.key)
    return ans


# Returns the commits relevant to bug_issue
def get_issue_commits(issue):
    ans = []
    for commit in all_commits:
        if is_associated_to_commit(issue,commit):
            ans.append(commit)
    if len(ans) == 0:
        raise bug.BugError('Couldn\'t find commits associated with ' + issue.key)
    return ans


# Returns the commit that solved the bug
def get_fixes(issue_commits, issue_tests):
    ans = []
    module_dir = git_dir
    if not issue_tests[0].get_module()=='':
        module_dir = issue_tests[0].get_module()
    test_cmd = 'mvn surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -Dtest='
    for test in issue_tests:
        if not test_cmd.endswith('='):
            test_cmd += ','
        test_cmd += test.get_name()
    for commit in issue_commits:
        tests_before = []
        tests_after = []
        parent = None
        for curr_parent in commit.parents:
            for branch in curr_parent.repo.branches:
                if branch.name == branch_inspected:
                    parent = curr_parent
                    break
        if parent == None:
            continue

        try:
            repo.git.add('.')
            repo.git.commit('-m', 'BugDataMiner run')
            repo.git.checkout(parent.hexsha)
        except git.exc.GitCommandError as e:
            pass
        os.system('mvn clean install -DskipTests'+' -f ' + module_dir)
        os.system(test_cmd + ' -f ' + module_dir)
        tests_before = test_parser.get_tests(project_dir=module_dir)
        repo.git.checkout(commit.hexsha)
        os.system('mvn clean install -DskipTests'+' -f ' + module_dir)
        os.system(test_cmd + ' -f ' + module_dir)
        tests_after = test_parser.get_tests(project_dir=module_dir)
        for test in tests_after:
            if test not in tests_before:
                tup = (commit.hexsha, test.get_name(), 'Created in commit')
                ans.append(tup)
            else:
                test_before = [t for t in tests_before if t==test][0]
                if not test_before.passed:
                    tup = ((commit.hexsha, test.get_name(), 'Fixed in commit'))
                    ans.append(tup)
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


# Return the test that the bug failed
def get_test(issue, relevant_tests):
    pass

def say_hello():
    return 'hello'

def set_up(git_url):
    global all_commits
    global all_tests
    global repo
    global git_dir
    global proj_name
    global bug_issues
    all_test_cache = cache_dir+'\\all_tests.pkl'
    all_commits_cache =  cache_dir+'\\all_commits.pkl'
    bug_issues_cache = cache_dir + '\\bug_issues'
    proj_name = git_url.rsplit('/', 1)[1]
    try:
        git.Git(os.getcwd()).clone(git_url)
    except git.exc.GitCommandError:
        pass
    git_dir = os.getcwd() + '\\' + proj_name
    # os.system('mvn install -f'+git_dir)
    repo = Repo(git_dir)
    all_tests = get_from_cache(all_test_cache,
                               lambda: test_parser.get_tests(os.getcwd() + '\\' + proj_name + '_installed'))
    # all_commits = get_from_cache(all_commits_cache,
    #                            lambda: list(repo.iter_commits(branch_inspected)))
    # bug_issues = get_from_cache(bug_issues_cache,
    #                             lambda: jira.search_issues('project=' + proj_name + ' and type=bug', maxResults=2500))
    all_commits = list(repo.iter_commits(branch_inspected))
    JQL_QUERY = 'project = {} AND issuetype = Bug AND text ~ test ORDER BY  createdDate ASC'.format(proj_name)
    bug_issues = jira.search_issues(JQL_QUERY, maxResults=MAX_ISSUES_TO_RETRIEVE)


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

if __name__ == '__main__':
    main(sys.argv[1:]);

# #Returns tests that fixed in commit
# def get_tests_fixed_in_commit(commit, all_tests):
#     ans = []
#     options = {
#         'server': 'https://issues.apache.org/jira'}
#     jira = JIRA(options)
#     projects = jira.projects()
#     if contains_jira_issue(commit):
#         issue_id = get_jira_issue(commit)
#         issue = jira.issue(issue_id)
#         possible_test_names = get_possible_tests_names(issue)
#         for possible_test_name in possible_test_names:
#             for test_name in all_tests:
#                 if possible_test_name in test_name:
#                     ans.append(possible_test_name)
#                     break
#     return ans

# Returns issue if on a commit that is associated with jiar issue
# def get_jira_issue(commit):
#     return commit.message.partition(' ')[0]

# Returns tests exist in the HEAD of repo
# def get_tests(repo):
#     ans = []
#     surefire_reports_dir =repo.working_tree_dir+"\\tika-parsers\\target\\surefire-reports" #should be replaced with somthing generic
#     for filename in os.listdir(surefire_reports_dir):
#         if filename.endswith(".xml"):
#             abs_path = os.path.join(surefire_reports_dir, filename)
#             tree = ET.parse(abs_path)
#             root = tree.getroot()
#             for testcase in root.findall('testcase'):
#                 ans.append(testcase.get('classname')+'@'+testcase.get('name'))
#     return ans

# Returns true if the commit is associated to a jira issue
# def contains_jira_issue(commit):
#     return commit.message.startswith('TIKA')

# Returns the commits in repo that has high liklihood of having a bug fix
# def extract_critical_commits(repo):
#     commits = list(repo.iter_commits('master'))
#     return [commit for commit in commits if "fix" in commit.message]
