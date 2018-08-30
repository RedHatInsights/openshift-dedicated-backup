#!/usr/bin/python3
import config
from git import Repo
from git.exc import GitCommandError
from logger import logging as log


class GitRepo(object):
    def __init__(self, remote, working_dir):
        log.info('Cloning git repo: {0} into: {1}'.format(remote, working_dir))
        self.remote = remote
        self.working_dir = working_dir

        ssh_cmd = 'ssh -i {0}'.format(config.GIT_SSH_PRIVATE_KEY_LOC)
        log.debug('ssh_cmd: {}'.format(ssh_cmd))
        self.repo = Repo.init(working_dir)
        self.repo.git.update_environment(GIT_SSH_COMMAND=ssh_cmd)

        self.origin = self.repo.create_remote('origin', self.remote)
        self.origin.fetch()
        self.repo.create_head('master', self.origin.refs.master).set_tracking_branch(
            self.origin.refs.master).checkout()

    def checkout_branch(self, branch_name):
        try:
            self.repo.create_head(branch_name, self.origin.refs[branch_name]).set_tracking_branch(
                self.origin.refs[branch_name]).checkout()
            self.repo.heads[branch_name].checkout()
        except (GitCommandError, IndexError, AttributeError):
            self.repo.git.checkout('-b', branch_name)
            self.repo.git.reset('--hard', 'origin/master')

    def commit_all(self, msg):
        try:
            self.repo.git.add('.')
            self.repo.git.commit('-m', msg)
        except GitCommandError:
            pass  # nothing to commit

    def push_all(self):
        self.repo.git.push('--all', 'origin')
