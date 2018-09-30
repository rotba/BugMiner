import os
import git
import bug.bug as my_bug

db = os.path.join(os.getcwd(), 'results')

class Applier(object):

    def __init__(self, project_url, path, issue=None):
        self._path = path
        proj_name = project_url.rsplit('/', 1)[1]
        data_dir = os.path.join(self._path, 'data')
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)
        self._data_handler = my_bug.Bug_data_handler(data_dir)
        git.Git(self._path).init()
        try:
            git.Git(self._path).clone(project_url)
        except git.exc.GitCommandError as e:
            if 'already exists and is not an empty directory.' in str(e):
                pass
        self._repo = git.Repo(os.path.join(self._path, proj_name))
        if not issue == None:
            self._data_handler.fetch_issue_data(issue)
        else:
            self._data_handler.fetch_all_data(os.path.join(db, proj_name+'\\data'))

    #Applies the bug on the project
    def apply(self, bug):
        buggy_commit = bug.parent
        patch_path = self.data_handler.get_patch(bug)
        self._repo.git.reset('--hard')
        self._repo.git.clean('-xdf')
        self._repo.git.checkout(buggy_commit)
        self._repo.git.execute(['git', 'apply', patch_path])

    # Gets all the bugs in issue_key/commit_hexsha
    def get_bugs(self, issue_key, commit_hexsha):
        return self.data_handler.get_bugs(issue_key, commit_hexsha)

    @property
    def data_handler(self):
        return self._data_handler

    @property
    def proj_dir(self):
        return self._repo.git_dir.strip('.git')
