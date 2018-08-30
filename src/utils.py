#!/usr/bin/python3
import config
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


def setup_git_repo(repo, working_dir):
    remove_dir(working_dir)
    git_repo = GitRepo(
        repo, working_dir)
    return git_repo


def cleanup_temp_files():
    remove_dir(config.BACKUP_GIT_WORKING_DIR)
    remove_dir(config.SECRET_GIT_WORKING_DIR)
    remove_file(config.temp_ssh_file)
    remove_file(config.temp_cert_file)
