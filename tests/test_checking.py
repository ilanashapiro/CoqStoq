"""
Test coqstoq checking proofs.
"""

from pathlib import Path

from coqstoq.check import Result, check_result, get_ground_truth, get_context, get_theorem_statement
from coqstoq import get_theorem_list, Split, get_theorem

import logging, sys

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

def gen_context():
    COQSTOQ_LOC = Path.cwd()
    for split in Split:
        theorems = get_theorem_list(split, COQSTOQ_LOC)
        for thm in theorems:
            v_file = thm.project.workspace / thm.path
            ctx_file = v_file.with_suffix('.ctx')
            context = get_context(thm, COQSTOQ_LOC)
            with open(ctx_file, 'w') as f:
                f.write(context)
# gen_context()

def gen_user_prompt():
    COQSTOQ_LOC = Path.cwd()
    for split in Split:
        theorems = get_theorem_list(split, COQSTOQ_LOC)
        for thm in theorems:
            v_file = thm.project.workspace / thm.path
            ctx_file = v_file.with_suffix('.ctx')
            with open(ctx_file, 'r') as f:
                context = f.read()
            user_prompt_file = v_file.with_suffix('.pmt')
            with open(user_prompt_file, 'w') as f:
                f.write(get_user_prompt_for_file(get_theorem_statement(thm,COQSTOQ_LOC), context))
# gen_user_prompt()

def test_check_result_single():
    COQSTOQ_LOC = Path.cwd()
    test_thm = get_theorem(Split.TEST, 0, COQSTOQ_LOC)
    print(test_thm)
    bad_proof = ""
    # print(get_context(test_thm, COQSTOQ_LOC))
    good_proof = get_ground_truth(test_thm, COQSTOQ_LOC)
    good_result = Result(test_thm, good_proof, 1)
    bad_result = Result(test_thm, bad_proof, 1)
    assert check_result(good_result, COQSTOQ_LOC)
    assert not check_result(bad_result, COQSTOQ_LOC)
# test_check_result_single()