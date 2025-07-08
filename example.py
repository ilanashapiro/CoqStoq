from __future__ import annotations
from typing import Optional, Type

import json
import requests
from typing import Any
from pathlib import Path
from dataclasses import dataclass
import multiprocessing
import logging

logger = logging.getLogger(__name__)

EXAMPLES_PATH = Path("coq-test-data.jsonl")
COQSTOQ_LOC = "."
TIMEOUT = 120


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

    try:
        response = session.post(url, json=request, timeout=TIMEOUT)
        if response.status_code != 200:
            return ErrorResult(error=f"Server did not respond with 200 OK: {response.status_code}")
        result_json = response.json()["result"]
        return load_checking_result(result_json) 
    except ConnectionError as e:
        logger.error("Connection error while checking proof. Its likely that the server is not running.")
        return ErrorResult(error=f"Connection error: {str(e)}")
    except requests.Timeout as e:
        logger.error("Request timed out while checking proof.")
        return ErrorResult(error=f"Timeout error: {str(e)}")





@dataclass
class Example:
    user_prompt: str
    split: str
    index: int
    ground_truth: str

    def get_verification_request(self, proof: str) -> Any:
        return {
            "jsonrpc": "2.0",
            "method": "check_proof",
            "params": {
                "split": self.split,
                "idx": self.index,
                "coqstoq_loc": COQSTOQ_LOC,
                "proof": proof,
                "timeout": TIMEOUT,
            },
            "id": 1,
        }


    @classmethod
    def from_json(cls, json_obj: Any) -> Example:
        return cls(
            user_prompt=json_obj["user_prompt"],
            split=json_obj["split"],
            index=json_obj["index"],
            ground_truth=json_obj["ground_truth"],
        )


def load_examples() -> list[Example]:
    examples: list[Example] = []
    with EXAMPLES_PATH.open("r") as fin:
        for line in fin:
            line_obj = json.loads(line)
            examples.append(Example.from_json(line_obj))
    return examples


def check_ground_truth(example: Example):
    result = check_proof(example.split, example.index, example.ground_truth)
    match result:
        case ErrorResult(error=err):
            logger.error(f"Error checking proof for example {example.split} with index {example.index}: {err}")
            return
        case VerificationResult(success=success, messages=messages):
            if not success:
                logger.error(f"Verification failed for example {example.split} with index {example.index}: {messages}")
                return
            logger.info(f"Verification succeeded for example {example.split} with index {example.index}: {messages}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename="test_ground_truth.log", filemode="w")
    examples = load_examples()

    with multiprocessing.Pool(24) as pool:
        results = pool.map(check_ground_truth, examples)



