"""
Test coqstoq checking proofs.
"""

from pathlib import Path

from coqstoq.check import Result, check_result, get_ground_truth
from coqstoq.scripts import get_theorem_list, get_theorem
from coqstoq.check import get_ground_truth, get_theorem_text, get_context

import logging, sys, json

sys.path.append("CoqStoq")
from api import get_theorem_info

def get_user_prompt_for_file(theorem, file_context):
    return f"""The theorem I'm trying to prove is \n```\n{theorem}\n```\n#####\n\nThe file context in which I'm writing the proof is \n```\n{file_context}\n```\n#####\n\nStart the proof with the following tactic:\n```\nProof\n```\n\n"""

# def test_check_result(): # Takes time too run.
#     TEST_NUM_PER_SPLIT = 1
#     COQSTOQ_LOC = Path.cwd()
#     for split in Split:
#         eval_theorems = get_theorem_list(split)
#         for et in eval_theorems[:TEST_NUM_PER_SPLIT]:
#             logging.info(
#                 f"Checking mock results for {et.project.workspace / et.path} @ line {et.theorem_end_pos}"
#             )
#             bad_proof = ""
#             good_proof = get_ground_truth(et, COQSTOQ_LOC)
#             good_result = Result(et, good_proof, 1)
#             bad_result = Result(et, bad_proof, 1)
#             assert check_result(good_result, COQSTOQ_LOC)
#             assert not check_result(bad_result, COQSTOQ_LOC)

def gen_user_prompt(split: str = "train-sft"):
    COQSTOQ_LOC = Path.cwd()
    theorem_list = get_theorem_list(split, COQSTOQ_LOC)
    user_prompts_list = []
    for index in range(len(theorem_list)):
        thrm_info = get_theorem_info(split, index)
        user_prompts_list.append({
            "split": split,
            "index": index,
            "user_prompt": get_user_prompt_for_file(thrm_info.theorem, thrm_info.prefix)
        })
        print(index, len(theorem_list))
    print("Generated user prompts for theorems in split:", split)

    user_prompts_file = f"user_prompts_{split}.jsonl"
    with open(user_prompts_file, "w") as file:
        for datum in user_prompts_list:
            file.write(json.dumps(datum, ensure_ascii=False) + "\n")
    print(f"Results saved to {user_prompts_file}.")
    
gen_user_prompt()

def test_check_result_single():
    COQSTOQ_LOC = Path.cwd()
    test_thm = get_theorem("val", 0, COQSTOQ_LOC)
    bad_proof = ""
    # print(get_context(test_thm, COQSTOQ_LOC))
    good_proof = get_ground_truth(test_thm, COQSTOQ_LOC)
    good_result = Result(test_thm, good_proof, 1)
    bad_result = Result(test_thm, bad_proof, 1)
    assert check_result(good_result, COQSTOQ_LOC)
    assert not check_result(bad_result, COQSTOQ_LOC)
# test_check_result_single()