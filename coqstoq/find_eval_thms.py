import os
import json
import argparse
from pathlib import Path

from coqstoq.eval_thms import Project, find_eval_theorems, CoqComplieError, TestTheorem

TEST_THMS_LOC = Path("test-theorems")


def save_theorems(project: Project, file: Path, thms: list[TestTheorem]):
    assert file.is_relative_to(project.workspace)
    file_relpath = file.relative_to(project.workspace)
    save_loc = (
        Path(project.split.thm_dir_name) / project.dir_name / file_relpath
    ).with_suffix(".json")
    if not save_loc.parent.exists():
        save_loc.parent.mkdir(parents=True)
    with open(save_loc, "w") as f:
        json.dump([thm.to_json() for thm in thms], f, indent=2)


def find_project_theormes(project: Project):
    # TODO: Would be nice to get a summary of which files did not compile
    print(project.workspace)
    for file in project.workspace.glob("**/*.v"):
        print(f"Checking {file}")
        try:
            thms = find_eval_theorems(project, file)
            print(f"Found {len(thms)} theorems in {file}")
            save_theorems(project, file, thms)
        except CoqComplieError as e:
            print(f"Could not compile {file}; Error: {e}")
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Project)
    args = parser.parse_args()
    find_project_theormes(args.project)
