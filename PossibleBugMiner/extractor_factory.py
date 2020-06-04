from jira_extractor import JiraExtractor
from sourceforge_extractor import SourceforgeExtractor


class ExtractorFactory(object):
	@classmethod
	def create(cls, issue_tracker_url, repo_dir, branch_inspected, issue_key=None, query=None):
		if cls.is_jira(issue_tracker_url):
			return JiraExtractor(repo_dir=repo_dir, jira_url=issue_tracker_url,branch_inspected=branch_inspected, issue_key=issue_key, query=query)
		elif cls.is_sourceforge(issue_tracker_url):
			return SourceforgeExtractor(repo_dir=repo_dir, branch_inspected=branch_inspected)
		else:
			return None

	@classmethod
	def is_jira(cls, issue_tracker_url):
		return 'jira' in issue_tracker_url

	@classmethod
	def is_sourceforge(cls, issue_tracker_url):
		return 'sourceforge' in issue_tracker_url