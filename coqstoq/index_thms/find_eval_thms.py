from __future__ import annotations
from typing import Optional
import subprocess
import yaml
import os
import json
import argparse
from typing import Any
from pathlib import Path
from dataclasses import dataclass
import multiprocessing as mp

import logging

from coqpyt.lsp.structs import ResponseError
from coqstoq.build.project import PREDEFINED_PROJECTS, HOARETUT, Project, Split
from coqstoq.index_thms.eval_thms import (
    find_eval_theorems,
    CoqComplieError,
    CoqCompileTimeoutError,
    EvalTheorem,
)

logger = logging.getLogger(__name__)

TEST_THMS_LOC = Path("test-theorems")
REPORTS_LOC = Path("test-theorems-reports")


def save_theorems(project: Project, file: Path, thms: list[EvalTheorem]):
    assert file.is_relative_to(project.workspace)
    file_relpath = file.relative_to(project.workspace)
    save_loc = (
        Path(project.split.thm_dir_name) / project.dir_name / file_relpath
    ).with_suffix(".json")
    if not save_loc.parent.exists():
        save_loc.parent.mkdir(parents=True)
    with open(save_loc, "w") as f:
        json.dump([thm.to_json() for thm in thms], f, indent=2)


@dataclass
class Task:
    project: Project 
    file: Path
    timeout: int

def get_predefined_tasks(coqstoq_loc: Path, timeout: int) -> list[Task]:
    tasks: list[Task] = []
    for project in PREDEFINED_PROJECTS:
        for file in project.workspace.glob("**/*.v"):
            if file.is_file():
                tasks.append(Task(project, file, timeout))
    return tasks


SPLITS = [Split.from_name("train-sft"), Split.from_name("train-rl")]
def get_arbitrary_tasks(coqstoq_loc: Path, timeout: int) -> list[Task]:
    tasks: list[Task] = []
    for split in SPLITS:
        for project_loc in (coqstoq_loc / split.dir_name).iterdir():
            project = Project(
                dir_name=project_loc.name,
                split=split,
                commit_hash=None,
                compile_args=[],
            )
            for file in project.workspace.glob("**/*.v"):
                if file.is_file():
                    tasks.append(Task(project, file, timeout))
    return tasks


def run_task(task: Task):
    logger.info(f"Checking {task.file}")
    try:
        thms = find_eval_theorems(task.project, task.file, task.timeout)
        logger.info(f"Found {len(thms)} theorems in {task.file}")
        save_theorems(task.project, task.file, thms)
    except CoqComplieError as e:
        logger.error(f"Could not compile {task.file}; Error: {e}")
    except CoqCompileTimeoutError as e:
        logger.error(f"Compilation timed out for {task.file}; Error: {e}")
    except ResponseError as e:
        logger.error(f"Got Coq-LSP response error for {task.file}.")
    except Exception as e:
        logger.error(f"Unexpected error for {task.file}: {e}")



TIMEOUT = 120
if __name__ == "__main__":
    COQSTOQ_LOC = Path.cwd()
    parser = argparse.ArgumentParser(description="Find eval theorems in Coq files.")
    parser.add_argument("--arbitrary", action="store_true", help="Use arbitrary projects.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.arbitrary:
        tasks = get_arbitrary_tasks(COQSTOQ_LOC, TIMEOUT)
    else:
        tasks = get_predefined_tasks(COQSTOQ_LOC, TIMEOUT)

    with mp.Pool(mp.cpu_count()) as pool:
        pool.map(run_task, tasks)
    
