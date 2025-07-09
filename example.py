from __future__ import annotations
from typing import Optional, Type

import json
import requests
from typing import Any
from pathlib import Path
from dataclasses import dataclass
import multiprocessing
import logging
from coqstoq.scripts import get_theorem 
from coqstoq.check import get_ground_truth

logger = logging.getLogger(__name__)

COQSTOQ_LOC = "."
TIMEOUT = 30 # 120


@dataclass
class VerificationResult:
    success: bool
    messages: list[str]

    @classmethod
    def from_json(cls, json_obj: Any) -> VerificationResult:
        score = json_obj["score"]
        assert score == 1 or score == 0, "Score must be 1 or 0"
        return cls(
            success=score == 1,
            messages=json_obj["messages"],
        )

@dataclass
class ErrorResult:
    error: str

    @classmethod
    def from_json(cls, json_obj: Any) -> ErrorResult:
        assert json_obj["score"] == -1
        assert len(json_obj["messages"]) == 1, "Error messages should contain exactly one message"
        return cls(
            error=json_obj["messages"][0],
        )


CheckingResult = VerificationResult | ErrorResult

def load_checking_result(json_obj: Any) -> CheckingResult:
    if json_obj["score"] == -1:
        return ErrorResult.from_json(json_obj)
    else:
        return VerificationResult.from_json(json_obj)


def check_proof(split: str, idx: int, proof: str) -> CheckingResult:
    url = f"http://localhost:8080"
    session = requests.Session()
    request: Any = {
        "jsonrpc": "2.0",
        "method": "check_proof",
        "params": {
            "split": split,
            "idx": idx,
            "coqstoq_loc": COQSTOQ_LOC,
            "proof": proof,
            "timeout": TIMEOUT,
        },
        "id": 1,
    }
    print(f"Checking INSIDE proof for split: {split}, index: {idx}")

    try:
        response = session.post(url, json=request, timeout=TIMEOUT)
        print("STATUS CODE:", response.status_code)
        if response.status_code != 200:
            return ErrorResult(error=f"Server did not respond with 200 OK: {response.status_code}")
        result_json = response.json()["result"]
        print("RESPONSE:", result_json['score'])
        return load_checking_result(result_json) 
    except ConnectionError as e:
        print("Connection error while checking proof. Its likely that the server is not running.")
        logger.error("Connection error while checking proof. Its likely that the server is not running.")
        return ErrorResult(error=f"Connection error: {str(e)}")
    except requests.Timeout as e:
        print("Request timed out while checking proof.")
        logger.error("Request timed out while checking proof.")
        return ErrorResult(error=f"Timeout error: {str(e)}")


@dataclass
class Task:
    split: str
    idx: int
    ground_truth: str

    @classmethod
    def from_json(cls, json_obj: Any) -> Task:
        return cls(
            split=json_obj["split"],
            idx=json_obj["index"],
            ground_truth=json_obj["ground_truth"],
        )

def check_ground_truth(task: Task) -> Any:
    result = check_proof(task.split, task.idx, task.ground_truth)
    match result:
        case ErrorResult(error=err):
            logger.error(f"Error checking proof for example {task.split} with index {task.idx}: {err}")
            return
        case VerificationResult(success=success, messages=messages):
            if not success:
                logger.error(f"Verification failed for example {task.split} with index {task.idx}: {messages}")
                return result
            logger.info(f"Verification succeeded for example {task.split} with index {task.idx}: {messages}")



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    EXAMPLES_LOC = Path("example-sft.json")

    with open(EXAMPLES_LOC, "r") as f:
        train_sft_examples = json.load(f)["theorems"]
    tasks = [Task.from_json(example) for example in train_sft_examples]

    # Parallel checking (Number of processes should match the number of server threads.)
    with multiprocessing.Pool(8) as pool:
        results = pool.map(check_ground_truth, tasks)