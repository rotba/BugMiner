import os
from mvnpy import mvn, TestObjects
try:
    from javadiff.CommitsDiff import CommitsDiff
except:
    from javadiff.javadiff.CommitsDiff import CommitsDiff


class Candidate(object):
    TESTS_DIFFS_IS_CRITERIA = False

    def __init__(self, issue, fix_commit, tests, diffed_components):
        self._issue = issue
        self._fix_commit = fix_commit
        self._tests = tests or []
        self._diffed_components = diffed_components
        self._commit_diff = None
        self._changed_methods = None

    @property
    def issue(self):
        return self._issue

    @property
    def fix_commit(self):
        return self._fix_commit

    @property
    def tests(self):
        return self._tests

    @property
    def diffed_components(self):
        return self._diffed_components

    def calc_changed_methods(self):
        if self._changed_methods is not None:
            return
        ans = []
        try:
            self._commit_diff = CommitsDiff(child=self.fix_commit, parent=self.get_parent(), analyze_source_lines=False)
        except AssertionError as e:
            raise e
        for file_diff in self._commit_diff.diffs:
            if file_diff.is_java_file():
                ans.append(file_diff)
        self._changed_methods = set(reduce(list.__add__, map(lambda d: d.get_changed_methods(), ans), []))

    def get_parent(self):
        ans = None
        for curr_parent in self.fix_commit.parents:
            for branch in curr_parent.repo.refs:
                if branch.name == 'master':
                    ans = curr_parent
                    break
        return ans

    def get_relevant_tests(self, repo):
        test_files = filter(lambda x: "test" in x[1] and x[0].endswith("java"),
                            map(lambda x: (os.path.join(repo.working_dir, x),
                                           os.path.normpath(x.lower()).replace(".java", "").replace(os.path.sep, ".")),
                                repo.git.ls_files().split()))
        diffs_packages = map(
            lambda x: os.path.normpath(x.replace(".java", "")).replace(os.sep, ".").split("org.")[1].lower(),
            self.diffed_components)
        diffs_packages = map(lambda x: ".".join(["org"] + x.split('.')[:-1]), diffs_packages)
        self.tests.extend(
            list(map(lambda x: x[0], filter(lambda x: any(map(lambda y: y in x[1], diffs_packages)), test_files))))
        commit_tests_object = list(map(lambda t_path: TestObjects.TestClass(t_path, self.fix_commit.repo.working_dir),
                                       filter(lambda t: os.path.exists(os.path.realpath(t)), self.tests)))
        commit_testcases = mvn.get_testcases(commit_tests_object)
        return commit_testcases
