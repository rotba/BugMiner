import unittest
import os
from urlparse import urlparse
from extractor import Extractor

import git
from sourceforge_extractor import SourceforgeExtractor

TESTED_PROJECT = os.path.join(os.getcwd(),'tested_projects')

class MyTestCase(unittest.TestCase):
	JFREECHART_URL = 'https://github.com/jfree/jfreechart'
	def test_something(self):
		self.assertEqual(True, True)

	def test_extracting_simple_buggy_commit(self):
		proj_url = MyTestCase.JFREECHART_URL
		proj_dir = self.set_up_proj(proj_url)
		extractor = SourceforgeExtractor(repo_dir=proj_dir, branch_inspected='master')
		possible_bugs = extractor.extract_possible_bugs()
		a = extractor.get_all_commits()
		x =1

	def set_up_proj(self, git_url):
		proj_name = os.path.basename(urlparse(git_url).path)
		proj_dir = os.path.join(TESTED_PROJECT,proj_name)
		if not os.path.isdir(proj_dir):
			os.mkdir(proj_dir)
			git.Git(TESTED_PROJECT).clone(git_url)
		return proj_dir


if __name__ == '__main__':
	unittest.main()
