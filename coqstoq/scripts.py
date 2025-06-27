from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
from enum import Enum

from coqstoq.build.project import Split, Project
from coqstoq.index_thms.eval_thms import EvalTheorem
from coqstoq.create_theorem_lists import load_reference_list

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


def to_eval_split(split: str) -> Split:
    if isinstance(split, str):
        return Split(f"{split}-repos", f"{split}-theorems")
    elif isinstance(split, Split):
        return split.value


def num_theorems(split: str, coqstoq_loc: Path) -> int:
    thm_list = load_reference_list(to_eval_split(split), coqstoq_loc)
    return len(thm_list)


def get_theorem(split: str, idx: int, coqstoq_loc: Path) -> EvalTheorem:
    thm_list = load_reference_list(to_eval_split(split), coqstoq_loc)
    thm_ref = thm_list[idx]
    eval_thms = get_eval_thms(coqstoq_loc / thm_ref.thm_path)
    return eval_thms[thm_ref.thm_idx]


def get_theorem_list(split: str, coqstoq_loc: Path) -> list[EvalTheorem]:
    split_val = to_eval_split(split)
    eval_thm_dict = get_all_eval_thms(split_val, coqstoq_loc)
    thm_list = load_reference_list(split_val, coqstoq_loc)
    eval_thms: list[EvalTheorem] = []
    for thm_ref in thm_list:
        eval_thms.append(eval_thm_dict[thm_ref.thm_path][thm_ref.thm_idx])
    return eval_thms
