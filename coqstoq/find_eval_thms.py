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
from coqstoq.eval_thms import (
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


def get_eval_thms(file: Path) -> list[EvalTheorem]:
    with open(file) as f:
        thms = json.load(f)
        return [EvalTheorem.from_json(thm) for thm in thms]


def get_all_eval_thms(split: Split, coqstoq_loc: Path) -> dict[Path, list[EvalTheorem]]:
    thm_loc = coqstoq_loc / split.thm_dir_name
    assert thm_loc.exists()
    all_thms: dict[Path, list[EvalTheorem]] = {}
    for thm_file_loc in thm_loc.glob("**/*.json"):
        assert thm_file_loc.is_relative_to(coqstoq_loc)
        rel_thm_file_loc = thm_file_loc.relative_to(coqstoq_loc)
        all_thms[rel_thm_file_loc] = get_eval_thms(thm_file_loc)
    return all_thms


@dataclass
class TheoremReport:
    successful_files: list[Path]
    errored_files: list[Path]
    timed_out_files: list[Path]
    lsp_error_files: list[Path]
    num_theorems: int

    def print_summary(self):
        print(
            f"Num Files: {len(self.successful_files)}; Num Theorems: {self.num_theorems}"
        )
        if 0 < len(self.errored_files):
            print("Compile Errors:" + "".join([f"\n\t{f}" for f in self.errored_files]))
        if 0 < len(self.timed_out_files):
            print(
                "Timeout Errors:" + "".join([f"\n\t{f}" for f in self.timed_out_files])
            )
        if 0 < len(self.lsp_error_files):
            print("LSP Errors:" + "".join([f"\n\t{f}" for f in self.lsp_error_files]))

    @property
    def unsuccessful_files(self):
        return self.errored_files + self.timed_out_files + self.lsp_error_files

    def to_json(self) -> Any:
        return {
            "successful_files": [str(f) for f in self.successful_files],
            "errored_files": [str(f) for f in self.errored_files],
            "timed_out_files": [str(f) for f in self.timed_out_files],
            "lsp_error_files": [str(f) for f in self.lsp_error_files],
            "num_theorems": self.num_theorems,
        }

    @classmethod
    def from_json(cls, data: Any) -> TheoremReport:
        return cls(
            [Path(f) for f in data["successful_files"]],
            [Path(f) for f in data["errored_files"]],
            [Path(f) for f in data["timed_out_files"]],
            [Path(f) for f in data["lsp_error_files"]],
            data["num_theorems"],
        )

@dataclass
class Task:
    project: Project 
    file: Path
    timeout: int

def get_tasks(timeout: int) -> list[Task]:
    tasks: list[Task] = []
    for project in PREDEFINED_PROJECTS:
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



def unique_names(projects: list[Project]) -> bool:
    names = set()
    for p in projects:
        if p.dir_name in names:
            return False
        names.add(p.dir_name)
    return True


def find_project(proj_name: str) -> Project:
    assert unique_names(PREDEFINED_PROJECTS)
    for p in PREDEFINED_PROJECTS:
        if p.dir_name == proj_name:
            return p
    raise ValueError(f"Could not find project with name {proj_name}")



TIMEOUT = 120

def get_commit_hash(project_dir: Path) -> Optional[str]:
    git_dir_out = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=project_dir,
        capture_output=True,
    )

    if git_dir_out.returncode != 0:
        return None

    git_dir = Path(git_dir_out.stdout.decode().strip())
    if git_dir.parent.resolve() != project_dir.resolve():
        return None

    commit_hash_bytes = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )

    if commit_hash_bytes.returncode != 0:
        return None

    commit_hash = commit_hash_bytes.stdout.decode().strip()
    return commit_hash



def read_yaml_compile_args(project_name: str, yaml_file: Path) -> list[str]:
     with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)
        assert project_name in data, f"Project {project_name} not found in {yaml_file}"
        assert "compile_args" in data[project_name], f"Project {project_name} does not have compile_args in {yaml_file}"
        compile_args = data[project_name]["compile_args"]
        return compile_args



if __name__ == "__main__":
    tasks = get_tasks(TIMEOUT)
    with mp.Pool(mp.cpu_count()) as pool:
        pool.map(run_task, tasks)