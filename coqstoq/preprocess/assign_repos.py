from __future__ import annotations
from typing import Any

import json
import random
from dataclasses import dataclass
from pathlib import Path

COMMITS_LOC = "commits.json"
ASSIGNMENT_LOC = "assignment.json"
NUM_SFT_REPOS = 200 

test_repos = [
    f"AbsInt/CompCert",
    f"coq-community/buchberger",
    f"coq-community/dblib",
    f"coq-community/coq-ext-lib",
    f"coq-community/fourcolor",
    f"coq-community/hoare-tut",
    f"coq-community/huffman",
    f"coq-community/math-classes",
    f"thery/PolTac",
    f"coq-community/reglang",
    f"coq-community/zorns-lemma",
    f"coq-contribs/zfc",
] 

val_repos = [
    f"coq-community/bertrand",
    f"coq-community/stalmarck",
    f"coq-community/coqeal",
    f"coq-community/graph-theory",
    f"coq-community/sudoku",
]

cutoff_repos = [
    f"ccz181078/Coq-BB5",
    f"PnVDiscord/PnVRocqLib",
]

@dataclass
class Repo:
    name: str
    commit: int


def load_repos() -> list[Repo]:
    repos: list[Repo] = []
    with open(COMMITS_LOC, "r") as f:
        obj = json.load(f)
        for name, commit in obj.items():
            repos.append(Repo(name=name, commit=commit))
    return repos


@dataclass
class Assignment:
    train_sft: list[str]
    train_rl: list[str]
    val: list[str]
    test: list[str]
    cutoff: list[str]

    def to_json(self) -> Any:
        return {
            "train_sft": self.train_sft,
            "train_rl": self.train_rl,
            "val": self.val,
            "test": self.test,
            "cutoff": self.cutoff,
        }
    
    @classmethod
    def from_json(cls, obj: Any) -> Assignment:
        return cls(
            train_sft=obj["train_sft"],
            train_rl=obj["train_rl"],
            val=obj["val"],
            test=obj["test"],
            cutoff=obj["cutoff"]
        )


def create_assignment(repos: list[Repo]) -> Assignment:
    test: list[str] = []
    available_repos = {repo.name for repo in repos}
    for test_repo in test_repos:
        assert test_repo in available_repos, f"Test repo {test_repo} not found in available repos."
        test.append(test_repo)
        available_repos.remove(test_repo)
        assert test_repo not in available_repos
    
    val: list[str] = []
    for val_repo in val_repos:
        assert val_repo in available_repos, f"Validation repo {val_repo} not found in available repos."
        val.append(val_repo)
        available_repos.remove(val_repo)
        assert val_repo not in available_repos
    
    cutoff: list[str] = []
    for cutoff_repo in cutoff_repos:
        assert cutoff_repo in available_repos, f"Cutoff repo {cutoff_repo} not found in available repos."
        cutoff.append(cutoff_repo)
        available_repos.remove(cutoff_repo)
        assert cutoff_repo not in available_repos
    
    assert len(available_repos) >= NUM_SFT_REPOS
    random.seed(0)
    sft_repos = random.sample(list(available_repos), NUM_SFT_REPOS)
    for sft_repo in sft_repos:
        assert sft_repo in available_repos, f"SFT repo {sft_repo} not found in available repos."
        available_repos.remove(sft_repo)
        assert sft_repo not in available_repos
    
    rl_repos = list(available_repos)
    return Assignment(
        train_sft=sft_repos,
        train_rl=rl_repos,
        val=val,
        test=test,
        cutoff=cutoff
    )


if __name__ == "__main__":
    repos = load_repos()
    assignment = create_assignment(repos)
    with open(ASSIGNMENT_LOC, "w") as f:
        json.dump(assignment.to_json(), f, indent=2)
    print("Assignment created successfully.")