
"""
Used to clone repositories off of github. 
Meant to be a one time use. 
These repos will be stored in a place where they can be downladed together.
"""
from dataclasses import dataclass

import os
import json
from pathlib import Path
import multiprocessing as mp
import subprocess

import logging
logger = logging.getLogger(__name__)

COMMITS_FILE = Path("commits.json")
SAVE_LOC = Path("repos")
ERROR_FILE = Path("logs/clone-error.log")

def log_error(error: str):
    logger.error(error)
    assert ERROR_FILE.exists(), "Error file does not exist. Please create logs directory."
    padded_error = error if error.endswith("\n") else f"{error}\n" 
    with ERROR_FILE.open("a") as fout:
        fout.write(padded_error)

class RepoError(Exception):
    pass

DELIMITER = "-@@-" 
def name_repo(repo: str) -> str:
    if DELIMITER in repo:
        raise RepoError(f"Repository name {repo} contains the delimiter {DELIMITER}. Need to change delimiter.")
    return repo.replace("/", DELIMITER)


@dataclass
class Task:
    repo: str
    commit: str


def clone_repo(task: Task):
    try:
        repo_name = name_repo(task.repo)
        subprocess.run(["git", "clone", f"git@github.com:{task.repo}.git", repo_name], cwd=SAVE_LOC)
        if not (SAVE_LOC / repo_name).exists():
            raise RepoError(f"Failed to clone {task.repo}. Directory {repo_name} does not exist.")
        subprocess.run(["git", "checkout", task.commit], cwd=(SAVE_LOC / repo_name))
    except Exception as e:
        log_error(f"Error cloning {task.repo}: {e}")


def get_tasks() -> list[Task]:
    with COMMITS_FILE.open("r") as fin:
        commits: dict[str, str] = json.load(fin)
    return [Task(repo=repo, commit=commit) for repo, commit in commits.items()]


if __name__ == "__main__":
    N_JOBS = mp.cpu_count() // 4
    if not ERROR_FILE.exists():
        ERROR_FILE.parent.mkdir(parents=True, exist_ok=True)
        ERROR_FILE.touch()
    if not SAVE_LOC.exists():
        SAVE_LOC.mkdir(parents=True, exist_ok=True)
    
    tasks = get_tasks()
    with mp.Pool(N_JOBS) as pool:
        pool.map(clone_repo, tasks)

