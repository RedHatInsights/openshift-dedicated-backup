#!/usr/bin/python3
from git_repo import GitRepo
from logger import logging as log
import os
import shutil


def create_dir(project_name):
    try:
        os.makedirs(project_name)
    except OSError:
        log.debug('{0} directory already exists.'.format(project_name))


def remove_dir(directory):
    try:
        shutil.rmtree(directory)
    except FileNotFoundError:
        pass


def remove_file(path):
    try:
        os.remove(path)
    except (FileNotFoundError, TypeError):
        pass


def backup_dir(working_dir):
    return working_dir + '/backup'


def secret_dir(working_dir):
    return working_dir + '/secret'


def setup_git_repos(backup_repo, secret_repo, working_dir, private_key=None):
    backup_dir_str = backup_dir(working_dir)
    secret_dir_str = secret_dir(working_dir)
    remove_dir(backup_dir_str)
    remove_dir(secret_dir_str)
    backup = GitRepo(
        backup_repo, backup_dir_str, private_key)
    secret = GitRepo(
        secret_repo, secret_dir_str, private_key)
    return backup, secret
