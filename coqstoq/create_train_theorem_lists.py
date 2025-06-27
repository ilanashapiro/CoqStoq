
"""
Like `create_theorem_lists.py` but we filter the data as follows:
- A theorem can only be added if its statement has not been seen before.
- A file is only eligible to be added if it has _no_ theorems that are in in the
  test or validation splits.
"""
import json
import random
from pathlib import Path
from dataclasses import dataclass
import logging

from coqstoq.build.project import Split
from coqstoq.index_thms.eval_thms import EvalTheorem
from coqstoq.create_theorem_lists import TheoremReference
from coqstoq.check import get_theorem_text
from coqstoq.scripts import get_theorem_list


logger = logging.getLogger(__name__)

GUARDED_SPLITS = ["val", "test", "cutoff"]
COQSTOQ_LOC = Path.cwd()
def get_guarded_set() -> set[str]:
    guarded_set: set[str] = set()
    for split in GUARDED_SPLITS:
        thm_list = get_theorem_list(split, COQSTOQ_LOC)
        for thm in thm_list:
            guarded_set.add(get_theorem_text(thm, COQSTOQ_LOC))
    return guarded_set


class GuardedError(Exception):
    pass


def file_is_legal(guarded_set: set[str], file_thms: list[EvalTheorem]) -> bool:
    for thm in file_thms:
        thm_text = get_theorem_text(thm, COQSTOQ_LOC)
        if thm_text in guarded_set:
            return False
    return True

@dataclass
class TrainLists:
    train_rl: list[TheoremReference]
    train_sft: list[TheoremReference]


TRAIN_RL_SPLIT = Split.from_name("train-rl")
TRAIN_SFT_SPLIT = Split.from_name("train-sft")
TRAIN_SPLITS = [TRAIN_RL_SPLIT, TRAIN_SFT_SPLIT]
def create_train_lists(guarded_set: set[str], seed: int) -> TrainLists:
    duplicate_set: set[str] = set()
    num_guarded_filtered = 0
    num_duplicate_filtered = 0
    total_theorems = 0
    theorem_lists: dict[str, list[TheoremReference]] = {s.dir_name: [] for s in TRAIN_SPLITS}
    for split in TRAIN_SPLITS:
        split_theorems_loc = COQSTOQ_LOC / split.thm_dir_name
        assert split_theorems_loc.exists()
        for thm_file_loc in split_theorems_loc.glob("**/*.json"):
            assert thm_file_loc.is_relative_to(COQSTOQ_LOC)
            rel_thm_file_loc = thm_file_loc.relative_to(COQSTOQ_LOC)
            with thm_file_loc.open("r") as fin:
                thms_obj = json.load(fin)
                eval_thms = [EvalTheorem.from_json(thm) for thm in thms_obj]
                total_theorems += len(eval_thms)
                if not file_is_legal(guarded_set, eval_thms):
                    num_guarded_filtered += len(eval_thms)
                    logger.info(
                        f"Guarded against {len(eval_thms)} theorems in {rel_thm_file_loc}. "
                        f"Total guarded filtered: {num_guarded_filtered}."
                    )
                    continue
                num_file_duplicates = 0
                for i, thm in enumerate(eval_thms):
                    thm_text = get_theorem_text(thm, COQSTOQ_LOC)
                    if thm_text in duplicate_set:
                        num_file_duplicates += 1
                        continue
                    theorem_lists[split.dir_name].append(TheoremReference(rel_thm_file_loc, i))
                    duplicate_set.add(thm_text)
                num_duplicate_filtered += num_file_duplicates
                if num_file_duplicates > 0:
                    logger.info(
                        f"Filtered {num_file_duplicates} duplicate theorems in {rel_thm_file_loc}. "
                        f"Total duplicate filtered: {num_duplicate_filtered}."
                    )
        random.seed(seed)
        random.shuffle(theorem_lists[split.dir_name])
    print(f"Total theorems processed: {total_theorems}.")
    print(f"Total guarded filtered: {num_guarded_filtered}.")
    print(f"Total duplicate filtered: {num_duplicate_filtered}.")
    return TrainLists(
        train_rl=theorem_lists[TRAIN_RL_SPLIT.dir_name],
        train_sft=theorem_lists[TRAIN_SFT_SPLIT.dir_name],
    )


def create_train_theorem_list(seed: int):
    train_lists = create_train_lists(get_guarded_set(), seed)
    with open(TRAIN_RL_SPLIT.theorem_list_loc, "w") as fout:
        json.dump([thm.to_json() for thm in train_lists.train_rl], fout, indent=2)
    with open(TRAIN_SFT_SPLIT.theorem_list_loc, "w") as fout:
        json.dump([thm.to_json() for thm in train_lists.train_sft], fout, indent=2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_train_theorem_list(seed=0)
