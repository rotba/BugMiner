import logging
import os
import re
from urlparse import urlparse

import settings
from candidate import Candidate
from commit_analyzer import IsBugCommitAnalyzer
from extractor import Extractor
from jira import JIRA
from jira import exceptions as jira_exceptions


class JiraExtractor(Extractor):
	MAX_ISSUES_TO_RETRIEVE = 1000
	WEAK_ISSUE_COMMIT_BINDING = False

	# def __init__(self, repo_dir, branch_inspected, jira_url, issue_key=None, query = None, use_cash = False):
	def __init__(self, repo_dir, branch_inspected, jira_url, issue_key=None, query=None, commit=None):
		super(JiraExtractor, self).__init__(repo_dir, branch_inspected)
		self.jira_url = urlparse(jira_url)
		self.jira_proj_name = os.path.basename(self.jira_url.path)
		self.issue_key = issue_key
		self.commit = commit
		self.query = query if query != None else self.generate_jql_find_bugs()
		self.jira = JIRA(options={'server': 'https://issues.apache.org/jira'})
		self.issues_d = self.get_data()

	def get_data(self):
		if self.commit:
			return {"-1", self.repo.commit(self.commit)}
		issues = []
		if self.issue_key:
			issues = [self.issue_key]
		else:
			issues = JiraExtractor.get_jira_issues(self.jira_proj_name, 'https://issues.apache.org/jira')
		return self.commits_and_issues(issues)

	@staticmethod
	def get_jira_issues(project_name, url, bunch=100):
		jira_conn = JIRA(url)
		all_issues = []
		extracted_issues = 0
		query = "project={0}".format(project_name)
		while True:
			issues = jira_conn.search_issues(query, maxResults=bunch, startAt=extracted_issues)
			all_issues.extend(map(lambda issue: issue.key.strip(), issues))
			extracted_issues = extracted_issues + bunch
			if len(issues) < bunch:
				break
		# return map(lambda issue: issue.key.strip(), filter(lambda issue: issue.fields.issuetype.name.lower() == 'bug', all_issues))
		return all_issues

	def commits_and_issues(self, issues):
		def replace(chars_to_replace, replacement, s):
			temp_s = s
			for c in chars_to_replace:
				temp_s = temp_s.replace(c, replacement)
			return temp_s

		def get_bug_num_from_comit_text(commit_text, issues_ids):
			text = replace("[]?#,:(){}", "", commit_text.lower())
			text = replace("-_", " ", text)
			for word in text.split():
				if word.isdigit():
					if word in issues_ids:
						return word
			return "0"

		def clean_commit_message(commit_message):
			if "git-svn-id" in commit_message:
				return commit_message.split("git-svn-id")[0]
			return commit_message

		issues_d = {}
		issues_ids = map(lambda issue: issue.split("-")[1], issues)
		java_commits = self.get_java_commits()
		for git_commit in java_commits:
			if not self.has_parent(git_commit):
				logging.info('commit {0} has no parent '.format(git_commit.hexsha))
				continue
			commit_text = clean_commit_message(git_commit.summary)
			bug_id = get_bug_num_from_comit_text(commit_text, issues_ids)
			if bug_id != '0':
				issues_d.setdefault(bug_id, []).append(git_commit)
			elif any(map(lambda x: 'test' in x, java_commits[git_commit])) and any(map(lambda x: 'test' not in x, java_commits[git_commit])):
				# check if it change a test file and java
				if self.issue_key is None:
					issues_d.setdefault("-1", []).append(git_commit)
		return issues_d

	# Returns tupls of (issue,commit,tests) that may contain bugs
	def extract_possible_bugs(self, check_trace=False):
		for bug_issue, issue_commits in sorted(self.issues_d.items(), key=lambda x: int(x[0]), reverse=True):
			logging.info("extract_possible_bugs(): working on issue " + bug_issue)
			if len(issue_commits) == 0:
				logging.info('Couldn\'t find commits associated with ' + bug_issue)
				continue
			for commit in issue_commits:
				analyzer = IsBugCommitAnalyzer(commit=commit, parent=self.get_parent(commit), repo=self.repo)
				if analyzer.is_bug_commit(check_trace):
					yield Candidate(issue=bug_issue, fix_commit=analyzer.commit.hexsha, tests=analyzer.get_test_paths(), diffed_components=analyzer.source_diffed_components)
				else:
					logging.info(
						'Didn\'t associate ' + bug_issue + ' and commit ' + commit.hexsha + ' with any test')

	# Returns the commits relevant to bug_issue
	def get_issue_commits(self, issue):
		return filter(
			lambda x: self.is_associated_to_commit(issue, x),
			self.get_all_commits()
		)

	# Returns true if the commit message contains the issue key exclusively
	def is_associated_to_commit(self, issue, commit):
		if settings.DEBUG:
			if commit.hexsha == 'af6fe141036d30bfd1613758b7a9fb413bf2bafc':
				return True
		if issue.key in commit.message:
			if JiraExtractor.WEAK_ISSUE_COMMIT_BINDING:
				if 'fix' in commit.message.lower():
					return True
			index_of_char_after_issue_key = commit.message.find(issue.key) + len(issue.key)
			if index_of_char_after_issue_key == len(commit.message):
				return True
			char_after_issue_key = commit.message[commit.message.find(issue.key) + len(issue.key)]
			return not char_after_issue_key.isdigit()
		elif re.search("This closes #{}".format(issue.key), commit.message):
			return True
		elif re.search("\[{}\]".format(issue.key), commit.message):
			return True
		else:
			return False

	def get_bug_issues(self):
		try:
			return self.jira.search_issues(self.query, maxResults=JiraExtractor.MAX_ISSUES_TO_RETRIEVE)
		except jira_exceptions.JIRAError as e:
			raise JiraErrorWrapper(msg=e.text, jira_error=e)

	def generate_jql_find_bugs(self):
		ans = 'project = {} ' \
		      'AND issuetype = Bug '.format(
			self.jira_proj_name)
		if self.issue_key != None:
			ans = 'issuekey = {} AND ' \
				      .format(self.issue_key) + ans
		return ans


class JiraExtractorException(Exception):
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return repr(self.msg)


class JiraErrorWrapper(JiraExtractorException):
	def __init__(self, msg, jira_error):
		super(JiraErrorWrapper, self).__init__(msg)
		self.jira_error = jira_error
