import os
import json
import argparse
from pathlib import Path
from dataclasses import dataclass

from coqstoq.predefined_projects import PREDEFINED_PROJECTS
from coqstoq.eval_thms import (
    Project,
    find_eval_theorems,
    CoqComplieError,
    CoqCompileTimeoutError,
    EvalTheorem,
)

TEST_THMS_LOC = Path("test-theorems")


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
class TheoremReport:
    successful_files: list[Path]
    errored_files: list[Path]
    timed_out_files: list[Path]


def find_project_theormes(project: Project, timeout: int) -> TheoremReport:
    print(project.workspace)
    successful_files: list[Path] = []
    errored_files: list[Path] = []
    timed_out_files: list[Path] = []
    for file in project.workspace.glob("**/*.v"):
        print(f"Checking {file}")
        try:
            thms = find_eval_theorems(project, file, timeout)
            print(f"Found {len(thms)} theorems in {file}")
            save_theorems(project, file, thms)
            successful_files.append(file)
        except CoqComplieError as e:
            print(f"Could not compile {file}; Error: {e}")
            errored_files.append(file)
            continue
        except CoqCompileTimeoutError as e:
            print(f"Compilation timed out for {file}; Error; {e}")
            timed_out_files.append(file)
            continue
    return TheoremReport(successful_files, errored_files, timed_out_files)


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=str)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    project = find_project(args.project)
    find_project_theormes(project, args.timeout)
