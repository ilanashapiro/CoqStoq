import subprocess
import time
import socket
import atexit
import argparse
import os
import sys
import json
from tqdm import tqdm
from torch.utils.data import Dataset
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--sample_n", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--num_gpus", type=int, default=2)
    args = parser.parse_args()

    print("Starting Coqstoq verification server...")
    # Start the Docker server in detached mode
    subprocess.run([
        "docker", "run", "--rm", "-d",
        "--name", "coqstoq-server",
        "-p", "8080:8080",
        "coqstoq-full",
        "poetry", "run", "python3",
        "coqstoq/checker_server/server.py", "train-rl", "77785", "."
    ], check=True)

    # Stop the server automatically when the script ends
    atexit.register(lambda: subprocess.run(["docker", "stop", "coqstoq-server"]))

    # Wait until the server is up
    def wait_until_ready(port=8080, timeout=30):
        start = time.time()
        while time.time() - start < timeout:
            try:
                with socket.create_connection(("localhost", port), timeout=1):
                    return
            except OSError:
                time.sleep(0.2)
        raise TimeoutError("Server did not start in time.")

    wait_until_ready()
    print("Server is running and ready!")

    # Load tokenizer and vLLM engine
    print(f"Loading tokenizer and checkpoint from {args.model_name}... ", end="")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    tokenizer.padding_side = "left"

    llm = LLM(model=args.model_name, dtype="bfloat16", max_model_len=16384, tensor_parallel_size=args.num_gpus)
    print("Complete!")

    # Load validation data
    with open(os.path.join(args.popai_eval_path, "popai_valid.json")) as file:
        valid_data = json.load(file)
        if args.debug:
            valid_data = valid_data[:100]

    # atexit will stop the container when the script exits
