from mvnpy import TestObjects

class ChangedFile(object):

	def __init__(self, testcases, diff, path):
		self._diff = diff
		self._path = path
		self._testcases = testcases

	@property
	def testcases(self):
		return self._testcases

	@property
	def diff(self):
		return self._diff

	@property
	def path(self):
		return self._path

	def remove_testcases(self, testcases):
		for t in testcases:
			self._testcases.remove(t)

class ErroredFile(object):

	def __init__(self, path):
		self._path = path
		self._errors = []

	@property
	def errors(self):
		return self._errors

	@property
	def path(self):
		return self._path

	def add_error(self, error):
		return self._errors.append(error)

	@classmethod
	def create(cls, path, errors, git_repo):
		testclass = TestObjects.TestClass(path, git_repo.working_dir)
		for error in errors:
			if ErroredFile.is_class_cross_cutting_error(error, testclass):
				return ErroredFile(error.path)
		return OnlyTestcasesErroredFile(path, ErroredFile.extract_related_testcases(testclass, errors))

	@classmethod
	def is_class_cross_cutting_error(cls, error, error_testclass):
		return not any([t.contains_line(error.line) for t in error_testclass.testcases])

	@classmethod
	def extract_related_testcases(cls, testclass, errors):
		return filter(
			lambda x: any(map(lambda y: x.contains_line(y.line), errors)),
			testclass.testcases
		)


class OnlyTestcasesErroredFile(ErroredFile):

	def __init__(self, path, testcases):
		super(OnlyTestcasesErroredFile, self).__init__(path)
		self._testcases = testcases

	@property
	def testcases(self):
		return self._testcases
