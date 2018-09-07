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
all_tests = []
all_commits = []
branch_inspected = 'master'
repo = None
git_dir = ''
proj_name = ''


def main(argv):
    bug_data_set = []
    git_url = argv[0]
    global all_commits
    global all_tests
    global repo
    global git_dir
    global proj_name
    proj_name = git_url.rsplit('/', 1)[1]
    try:
        git.Git(os.getcwd()).clone(git_url)
    except git.exc.GitCommandError:
        pass
    git_dir = os.getcwd() + '\\' + proj_name
    # os.system('mvn install -f'+git_dir)
    repo = Repo(git_dir)
    bug_issues = jira.search_issues('project=' + proj_name + ' and type=bug', maxResults=2500)
    all_tests = test_parser.get_tests('C:\\Users\\user\\Code\\Python\\BugMiner\\tikaCopy')
    all_commits = list(repo.iter_commits(branch_inspected))
    for bug_issue in bug_issues:
        try:
            issue_tests = get_issue_tests(bug_issue)
            issue_commits = get_issue_commits(bug_issue)
            fixes = get_fixes(issue_commits, issue_tests)
            # diffs = get_diffs(commit, test)
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
    test_words = ['test', 'TEST', 'Test']
    if hasattr(issue.fields, 'description') and issue.fields.description != None:
        description = issue.fields.description.split(" ")
        for word in description:
            if any(x in word for x in test_words):
                if not word in test_words:  # make sure word is not triviale test word
                    test_names.append(word)
    if hasattr(issue.fields, 'attachment'):
        attachments = issue.fields.attachment
        for attachment in attachments:
            if any(x in attachment.filename for x in test_words):
                if not attachment.filename in test_words:  # make sure attachment.filename is not triviale test word
                    test_names.append(os.path.splitext(attachment.filename)[0])

    for test_name in test_names:
        for test in all_tests:
            if test_name in test.get_name():
                ans.append(test_name)
                break
    if len(ans) == 0:
        raise bug.BugError('Couldn\'t find tests associated with ' + issue.key)
    return ans


# Returns the commits relevant to bug_issue
def get_issue_commits(issue):
    ans = []
    for commit in all_commits:
        if issue.key in commit.message:
            ans.append(commit)
    if len(ans) == 0:
        raise bug.BugError('Couldn\'t find commits associated with ' + issue.key)
    return ans


# Returns the commit that solved the bug
def get_fixes(issue_commits, issue_tests):
    ans = {}
    test_cmd = 'mvn surefire:test -DfailIfNoTests=false -DtestFailureIgnore=true -Dtest='
    for test in issue_tests:
        if not test_cmd.endswith('='):
            test_cmd += ','
        test_cmd += test
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
            repo.index.add('.')
        except git.exc.GitCommandError:
            pass
        repo.git.checkout(parent.hexsha)
        os.system(test_cmd + ' -f ' + git_dir)
        tests_before = test_parser.get_tests(project_dir=git_dir)
        x = 1


# Return the test that the bug failed
def get_test(issue, relevant_tests):
    pass


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
