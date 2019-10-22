import os
BASE_DIR = os.getcwd()
TESTED_PROJECTS_DIR = os.path.join(BASE_DIR , 'tested_projects')
RESULTS_DIR = os.path.join(BASE_DIR , 'results')

class ProjFiles(object):
	def __init__(self, proj_name):
		self.base = os.path.join(TESTED_PROJECTS_DIR, proj_name)
		self.repo = os.path.join(self.base, proj_name)
		self.tmp = os.path.join(self.base, 'tmp_files')
		self.patches = os.path.join(self.tmp, 'patches')
		self.cache = os.path.join(self.base, 'cache')
		self.states = os.path.join(self.cache, 'states')
