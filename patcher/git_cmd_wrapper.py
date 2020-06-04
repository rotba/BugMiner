# Wraps git command. Handles excpetions mainly
import logging
import time

import git


def git_cmds_wrapper(git_cmd, repo):
	try:
		git_cmd()
	except git.exc.GitCommandError as e:
		if 'Another git process seems to be running in this repository, e.g.' in str(e):
			logging.info(str(e))
			time.sleep(2)
			git_cmds_wrapper(lambda: git_cmd())
		elif 'nothing to commit, working tree clean' in str(e):
			pass
		elif 'Please move or remove them before you switch branches.' in str(e):
			logging.info(str(e))
			git_cmds_wrapper(lambda: repo.index.add('.'))
			git_cmds_wrapper(lambda: repo.git.clean('-xdf'))
			git_cmds_wrapper(lambda: repo.git.reset('--hard'))
			time.sleep(2)
			git_cmds_wrapper(lambda: git_cmd())
		elif 'already exists and is not an empty directory.' in str(e):
			pass
		elif 'warning: squelched' in str(e) and 'trailing whitespace.' in str(e):
			pass
		else:
			raise e