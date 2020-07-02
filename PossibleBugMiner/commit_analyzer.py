import logging
from pathlib import Path
import os
try:
    from javadiff.CommitsDiff import CommitsDiff
except:
    from javadiff.javadiff.CommitsDiff import CommitsDiff


class IsBugCommitAnalyzer(object):
    TESTS_DIFFS_IS_CRITERIA = False

    def __init__(self, commit, parent, repo, diffed_files):
        self._commit = commit
        self._parent = parent
        self._repo = repo
        self.diffed_files = diffed_files
        self.associated_tests_paths = None
        self.diffed_components = None
        self.source_diffed_components = None
        self.changed_exists_methods = None
        self.changed_methods = None

    @property
    def commit(self):
        return self._commit

    @property
    def parent(self):
        return self._parent

    def analyze(self):
        if len(self.commit.parents) == 0: return self
        return self

    def is_bug_commit(self, check_trace=False):
        # if settings.DEBUG:
        #     if self.commit.hexsha == 'af6fe141036d30bfd1613758b7a9fb413bf2bafc':
        #         return True
        if not self.has_associated_diffed_components():
            logging.info('commit {0} has no diffed components'.format(self.commit.hexsha))
            return False
        if not self.has_associated_tests_paths():
            logging.info('commit {0} has not associated test paths'.format(self.commit.hexsha))
            return False
        # if self.has_added_methods():
        #     logging.info('commit {0} has new methods'.format(self.commit.hexsha))
        #     return False
        self.associated_tests_paths = self.get_tests_paths_from_commit()
        if check_trace:
            import mvnpy.Repo
            repo = mvnpy.Repo.Repo(self._repo.working_dir)
            if repo.has_surefire():
                return True
        return True

    def get_test_paths(self):
        return self.associated_tests_paths

    def has_added_methods(self):
        # check of there are new non-test methods
        for file_diff in self.diffed_components:
            changed_exists = file_diff.get_changed_exists_methods()
            for m in file_diff.get_changed_methods():
                if "test" not in m.id.lower() and m not in changed_exists:
                    return True
        return False

    def get_tests_paths_from_commit(self):
        ans = []
        for file_diff in self.diffed_files:
            if self.is_test_file(file_diff):
                ans.append(os.path.join(self._repo.working_dir, file_diff))
        return ans

    def has_associated_tests_paths(self):
        if not IsBugCommitAnalyzer.TESTS_DIFFS_IS_CRITERIA: return True
        self.associated_tests_paths = self.get_tests_paths_from_commit()
        return self.associated_tests_paths is not None and len(self.associated_tests_paths) > 0

    def has_associated_diffed_components(self):
        # self.diffed_components = self.get_diffed_components()
        self.source_diffed_components = list(filter(lambda x: not self.is_test_file(x), self.diffed_files))
        return self.source_diffed_components is not None and len(self.source_diffed_components) > 0

    def is_test_file(self, file):
        name = os.path.basename(file.lower())
        if not name.endswith('.java'):
            return False
        if name.endswith('test.java'):
            return True
        if name.endswith('tests.java'):
            return True
        if name.startswith('test'):
            return True
        if 'test' in os.path.basename(file).lower() and 'test' in Path(file).parts:
            return True
        return False

    def get_diffed_components(self):
        ans = []
        try:
            commit_diff = CommitsDiff(child=self.commit, parent=self.parent, analyze_source_lines=False)
        except AssertionError as e:
            raise e
        for file_diff in commit_diff.diffs:
            if file_diff.is_java_file():
                ans.append(file_diff)
        return ans
