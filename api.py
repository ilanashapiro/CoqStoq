"""
Exposes the following commands
"""
from typing import Any

import sys
import json
import argparse
from dataclasses import dataclass
from pathlib import Path

from coqstoq.check import get_ground_truth, get_prefix, get_suffix, get_theorem_text
from coqstoq.scripts import num_theorems, get_theorem, get_theorem_list

COQSTOQ_LOC = Path.cwd()

@dataclass
class GetSplitsResult:
    splits: list[str]

    def to_json(self) -> Any:
        return {"splits": self.splits} 

def get_splits() -> GetSplitsResult:
    return GetSplitsResult(splits=["train-sft", "train-rl", "val", "cutoff", "test"])

@dataclass
class GetNumTheoremsResult:
    num_theorems: int

    def to_json(self) -> Any:
        return {"num_theorems": self.num_theorems}

def get_num_theorems(split: str) -> GetNumTheoremsResult:
    return GetNumTheoremsResult(num_theorems=num_theorems(split, COQSTOQ_LOC))

@dataclass
class GetTheoremInfoResult:
    split: str
    index: int
    prefix: str
    suffix: str
    theorem: str
    ground_truth: str

    def to_json(self) -> Any:
        return {
            "split": self.split,
            "index": self.index,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "theorem": self.theorem,
            "ground_truth": self.ground_truth,
        }



def get_theorem_info(split: str, idx: int) -> GetTheoremInfoResult:
    theorem_info = get_theorem(split, idx, COQSTOQ_LOC)
    ground_truth = get_ground_truth(theorem_info, COQSTOQ_LOC)
    prefix = get_prefix(theorem_info, COQSTOQ_LOC)
    suffix = get_suffix(theorem_info, COQSTOQ_LOC)
    theorem = get_theorem_text(theorem_info, COQSTOQ_LOC)
    return GetTheoremInfoResult(
        split=split,
        index=idx,
        prefix=prefix,
        suffix=suffix,
        theorem=theorem,
        ground_truth=ground_truth,
    )


@dataclass
class GetTheoremRangeResult:
    theorems: list[GetTheoremInfoResult]

    def to_json(self) -> Any:
        return {
            "theorems": [thm.to_json() for thm in self.theorems]
        }


def handle_get_splits(args: argparse.Namespace) -> None:
    result = get_splits()
    json_str = json.dumps(result.to_json(), indent=2)
    sys.stdout.write(json_str)
    sys.stdout.flush()

def handle_get_num_theorems(args: argparse.Namespace) -> None:
    split = args.split
    result = get_num_theorems(split)
    json_str = json.dumps(result.to_json(), indent=2)
    sys.stdout.write(json_str)
    sys.stdout.flush()

def handle_get_theorem_info(args: argparse.Namespace) -> None:
    split = args.split
    index = args.index
    result = get_theorem_info(split, index)
    json_str = json.dumps(result.to_json(), indent=2)
    sys.stdout.write(json_str)
    sys.stdout.flush()

def handle_get_theorem_range(args: argparse.Namespace) -> None:
    split = args.split
    start = args.start
    end = args.end
    assert start <= end, "Start index must be less than or equal to end index"
    all_theorems = get_theorem_list(split, COQSTOQ_LOC)
    assert 0 <= start, f"Start index must be non-negative, got {start}"
    assert start < len(all_theorems), f"Start index is out of bounds. Must be less than {len(all_theorems)}"
    assert 0 <= end, f"End index must be non-negative, got {end}"
    assert end <= len(all_theorems), f"End index must be less than or equal to {len(all_theorems)}"
    sub_theorems = all_theorems[start:end]
    thm_infos: list[GetTheoremInfoResult] = []
    for i, thm in enumerate(sub_theorems):
        ground_truth = get_ground_truth(thm, COQSTOQ_LOC)
        prefix = get_prefix(thm, COQSTOQ_LOC)
        suffix = get_suffix(thm, COQSTOQ_LOC)
        theorem = get_theorem_text(thm, COQSTOQ_LOC)
        thm_info = GetTheoremInfoResult(
            split=split,
            index=start + i,
            prefix=prefix,
            suffix=suffix,
            theorem=theorem,
            ground_truth=ground_truth,
        )
        thm_infos.append(thm_info)
    result = GetTheoremRangeResult(theorems=thm_infos)
    json_str = json.dumps(result.to_json(), indent=2)
    sys.stdout.write(json_str)
    sys.stdout.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoqStoq API")
    subparsers = parser.add_subparsers(dest="command", required=True)

    splits_parser = subparsers.add_parser("get_splits", help="Get available splits")
    splits_parser.set_defaults(func=handle_get_splits)

    num_thms_parser = subparsers.add_parser("get_num_theorems", help="Get number of theorems in a split")
    num_thms_parser.add_argument("split", type=str, help="Split name (e.g., 'train-sft', 'train-rl', 'val', 'test', 'cutoff')")
    num_thms_parser.set_defaults(func=handle_get_num_theorems)

    thm_info_parser = subparsers.add_parser("get_theorem_info", help="Get information about a theorem")
    thm_info_parser.add_argument("split", type=str, help="Split name (e.g., 'train-sft', 'train-rl', 'val', 'test', 'cutoff')")
    thm_info_parser.add_argument("index", type=int, help="Index of the theorem in the split")
    thm_info_parser.set_defaults(func=handle_get_theorem_info)

    thm_range_parser = subparsers.add_parser("get_theorem_range", help="Get a range of theorems from a split")
    thm_range_parser.add_argument("split", type=str, help="Split name (e.g., 'train-sft', 'train-rl', 'val', 'test', 'cutoff')")
    thm_range_parser.add_argument("start", type=int, help="Start index of the theorem range")
    thm_range_parser.add_argument("end", type=int, help="End index of the theorem range (exclusive)")
    thm_range_parser.set_defaults(func=handle_get_theorem_range)

    args = parser.parse_args()
    args.func(args)




