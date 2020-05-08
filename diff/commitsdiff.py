
from FileDiff import FileDiff


class CommitsDiff(object):
    def __init__(self, commit_a, commit_b):
        self.diffs = list(CommitsDiff.diffs(commit_a, commit_b))

    @staticmethod
    def diffs(commit_a, commit_b):
        for d in commit_a.tree.diff(commit_b.tree, ignore_blank_lines=True, ignore_space_at_eol=True):
            try:
                yield FileDiff(d, commit_b.hexsha)
            except:
                pass
