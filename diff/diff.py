import StringIO
import gc
import json
import sys

import git
import jira

from CommitsDiff import CommitsDiff
from FileDiff import FileDiff


def get_changed_methods(git_path, child, parent=None):
    repo = git.Repo(git_path)
    if isinstance(child, str):
        child = repo.commit(child)
    if not parent:
        parent = child.parents[0]
    repo_files = filter(lambda x: x.endswith(".java") and not x.lower().endswith("test.java"),
                        repo.git.ls_files().split())
    return get_methods_from_file_diffs(CommitsDiff(child, parent).diffs)


def get_modified_functions(git_path):
    repo = git.Repo(git_path)
    diffs = repo.head.commit.tree.diff(None, None, True, ignore_blank_lines=True, ignore_space_at_eol=True)
    return get_methods_from_file_diffs(map(lambda d: FileDiff(d, repo.head.commit.hexsha, git_dir=git_path), diffs))


def get_methods_from_file_diffs(file_diffs):
    methods = []
    for file_diff in file_diffs:
        gc.collect()
        if file_diff.is_java_file():
            methods.extend(file_diff.get_changed_methods())
    return methods


def get_methods_descriptions(git_path, json_out_file):
    repo = git.Repo(git_path)
    repo_files = filter(lambda x: x.endswith(".java") and not x.lower().endswith("test.java"),
                        repo.git.ls_files().split())
    commits_to_check = reduce(set.__or__,
                              map(lambda file_name: set(repo.git.log('--pretty=format:%h', file_name).split('\n')),
                                  repo_files), set())
    commit_size = min(set(map(lambda x: len(x), commits_to_check)))
    commits_to_check = map(lambda x: x[:commit_size], commits_to_check)
    commits = list(repo.iter_commits())
    methods_descriptions = {}
    print "# commits to check: {0}".format(len(commits_to_check))
    for i in range(len(commits) - 1):
        print "commit {0} of {1}".format(i, len(commits))
        if not commits[i + 1].hexsha[:commit_size] in commits_to_check:
            continue
        print "inspect commit {0} of {1}".format(i, len(commits))
        methods = get_changed_methods(git_path, commits[i + 1])
        if methods:
            map(lambda method: methods_descriptions.setdefault(method, StringIO.StringIO()).write(
                commits[i + 1].message), methods)
    with open(json_out_file, "wb") as f:
        data = dict(map(lambda x: (x[0], x[1].getvalue()), methods_descriptions.items()))
        json.dump(data, f)


def get_jira_issues(project_name, url, bunch=100):
    jira_conn = jira.JIRA(url)
    all_issues = []
    extracted_issues = 0
    while True:
        issues = jira_conn.search_issues("project={0}".format(project_name), maxResults=bunch, startAt=extracted_issues)
        all_issues.extend(filter(lambda issue: issue.fields.description, issues))
        extracted_issues = extracted_issues + bunch
        if len(issues) < bunch:
            break
    return dict(map(lambda issue: (issue.key.strip().split("-")[1].lower(), (
    issue.fields.issuetype.name.lower(), issue.fields.description.encode('utf-8').lower())), all_issues))


def clean_commit_message(commit_message):
    if "git-svn-id" in commit_message:
        return commit_message.split("git-svn-id")[0]
    return commit_message


def commits_and_issues(gitPath, issues):
    def get_bug_num_from_comit_text(commit_text, issues_ids):
        s = commit_text.lower().replace(":", "").replace("#", "").replace("-", " ").replace("_", " ").split()
        for word in s:
            if word.replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('{', '').replace('}',
                                                                                                                 '').isdigit():
                if word in issues_ids:
                    return word
        return "0"

    commits = []
    issues_per_commits = dict()
    repo = git.Repo(gitPath)
    for git_commit in repo.iter_commits():
        commit_text = clean_commit_message(git_commit.message)
        issue_id = get_bug_num_from_comit_text(commit_text, issues.keys())
        if issue_id != "0":
            methods = get_changed_methods(gitPath, git_commit)
            if methods:
                issues_per_commits.setdefault(issue_id, (issues[issue_id], []))[1].extend(methods)
    return issues_per_commits


def get_bugs_data(gitPath, jira_project_name, jira_url, json_out, number_of_bugs=100):
    issues = get_jira_issues(jira_project_name, jira_url)
    issues = dict(map(lambda issue: (issue, issues[issue][1]), filter(lambda issue: issues[issue][0] == 'bug', issues)))
    with open(json_out, "wb") as f:
        json.dump(commits_and_issues(gitPath, issues), f)


if __name__ == "__main__":
    funtions = get_modified_functions(r"C:\amirelm\component_importnace\data\maven\clones\5209_87884c7b")
    print funtions
    exit()
    args = sys.argv
    c = get_changed_methods(r"C:\Temp\commons-lang",
                              git.Repo(r"C:\Temp\commons-lang").commit("38140a5d8dffec88f7c88da73ce3989770e086e6"))
    for c1 in c:
        print c1
        print "\n\t".join(map(repr, c1.get_changed_lines()))
    assert len(args) == 6, "USAGE: diff.py git_path jira_project_name jira_url json_method_file json_bugs_file"
    get_bugs_data(args[1], args[2], args[3], args[5])
    get_methods_descriptions(args[1], args[4])
