from typing import Any

import json
import argparse
import logging
from pathlib import Path

from coqstoq.preprocess.assign_repos import Assignment

logger = logging.getLogger(__name__)

ASSIGNMENT_LOC = Path("assignment.json")
DELIM = "-@@-"

def load_assignment() -> Assignment:
    with open(ASSIGNMENT_LOC, "r") as f:
        json_data = json.load(f) 
    return Assignment.from_json(json_data)


name_conversion = {
    # Test
    "AbsInt/CompCert": "compcert",
    "coq-community/buchberger": "buchberger",
    "coq-community/dblib": "dblib",
    "coq-community/coq-ext-lib": "ext-lib",
    "coq-community/fourcolor": "fourcolor",
    "coq-community/hoare-tut": "hoare-tut",
    "coq-community/huffman": "huffman",
    "coq-community/math-classes": "math-classes",
    "thery/PolTac": "poltac",
    "coq-community/reglang": "reglang",
    "coq-community/zorns-lemma": "zorns-lemma",
    "coq-contribs/zfc": "zfc",

    # Val
    "coq-community/bertrand": "bertrand",
    "coq-community/stalmarck": "stalmarck",
    "coq-community/coqeal": "coqeal",
    "coq-community/graph-theory": "graph-theory",
    "coq-community/sudoku": "sudoku",
    "coq-community/qarith-stern-brocot": "qarith-stern-brocot",

    # Cutoff
    "ccz181078/Coq-BB5": "bb5",
    "PnVDiscord/PnVRocqLib": "pnvrocqlib",
}

def name_repo(repo: str, convert:bool =False) -> str:
    if convert and repo in name_conversion:
        return name_conversion[repo]
    assert not DELIM in repo, f"Repository name {repo} contains the delimiter {DELIM}."
    return repo.replace("/", DELIM)


def move_repos(flat_repos_loc: Path, coqstoq_loc: Path, assignment: Assignment):
    VAL_LOC = coqstoq_loc / "val-repos"
    TEST_LOC = coqstoq_loc / "test-repos"
    CUTOFF_LOC = coqstoq_loc / "cutoff-repos"
    TRAIN_SFT_LOC = coqstoq_loc / "train-sft-repos"
    TRAIN_RL_LOC = coqstoq_loc / "train-rl-repos"

    VAL_LOC.mkdir(parents=True, exist_ok=True)
    TEST_LOC.mkdir(parents=True, exist_ok=True)
    CUTOFF_LOC.mkdir(parents=True, exist_ok=True)
    TRAIN_SFT_LOC.mkdir(parents=True, exist_ok=True)
    TRAIN_RL_LOC.mkdir(parents=True, exist_ok=True)

    for val_repo in assignment.val:
        flat_loc = flat_repos_loc / name_repo(val_repo)
        assert flat_loc.exists(), f"Validation repo {val_repo} not found in flat repos location {flat_repos_loc}."
        new_loc = coqstoq_loc / "val-repos" / name_repo(val_repo, convert=True)
        flat_loc.rename(new_loc)
    
    for test_repo in assignment.test:
        flat_loc = flat_repos_loc / name_repo(test_repo)
        assert flat_loc.exists(), f"Test repo {test_repo} not found in flat repos location {flat_repos_loc}."
        new_loc = coqstoq_loc / "test-repos" / name_repo(test_repo, convert=True)
        flat_loc.rename(new_loc)
    
    for cutoff_repo in assignment.cutoff:
        flat_loc = flat_repos_loc / name_repo(cutoff_repo)
        assert flat_loc.exists(), f"Cutoff repo {cutoff_repo} not found in flat repos location {flat_repos_loc}."
        new_loc = coqstoq_loc / "cutoff-repos" / name_repo(cutoff_repo, convert=True)
        flat_loc.rename(new_loc)
    
    for train_sft_repo in assignment.train_sft:
        flat_loc = flat_repos_loc / name_repo(train_sft_repo)
        if not flat_loc.exists():
            logger.warning(f"Train SFT repo {train_sft_repo} not found in flat repos location {flat_repos_loc}. Skipping.")
            continue
        new_loc = coqstoq_loc / "train-sft-repos" / name_repo(train_sft_repo)
        flat_loc.rename(new_loc)
    
    for train_rl_repo in assignment.train_rl:
        flat_loc = flat_repos_loc / name_repo(train_rl_repo)
        if not flat_loc.exists():
            logger.warning(f"Train RL repo {train_rl_repo} not found in flat repos location {flat_repos_loc}. Skipping.")
            continue
        new_loc = coqstoq_loc / "train-rl-repos" / name_repo(train_rl_repo)
        flat_loc.rename(new_loc)
    
    assert len(list(flat_repos_loc.iterdir())) == 0, f"Flat repos location {flat_repos_loc} is not empty after moving repositories."

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("flat_repos_loc", type=str, help="Path to the flat repos location")
    parser.add_argument("coqstoq_loc", type=str, help="Path to the CoqStoq location")

    args = parser.parse_args()
    flat_repos_loc = Path(args.flat_repos_loc)
    coqstoq_loc = Path(args.coqstoq_loc)

    assert flat_repos_loc.exists(), f"Flat repos location {flat_repos_loc} does not exist."
    assert coqstoq_loc.exists(), f"CoqStoq location {coqstoq_loc} does not exist."

    assignment = load_assignment()
    move_repos(flat_repos_loc, coqstoq_loc, assignment)