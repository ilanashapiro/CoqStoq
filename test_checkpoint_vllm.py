import subprocess
import time
import socket
import atexit
import argparse
import os
import sys
import json
import requests
from tqdm import tqdm
from torch.utils.data import Dataset
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

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

def start_coq_verification_server():
    subprocess.run([
            "docker", "run", "--rm", "-d",
            "--name", "coqstoq-server",
            "-p", "8080:8080",
            "coqstoq-full",
            "poetry", "run", "python3",
            "coqstoq/checker_server/server.py", "test", "77785", "."
        ], check=True)

    # Stop the server automatically when the script ends
    atexit.register(lambda: subprocess.run(["docker", "stop", "coqstoq-server"]))
    wait_until_ready()

def check_proof(proof: str) -> dict:
    """
    Start the verification server if necessary, then POST the given proof.
    Returns the parsed JSON‑RPC response as a Python dict.
    """
    start_coq_verification_server()
    wait_until_ready()

    payload = {
        "jsonrpc": "2.0",
        "method":  "check_proof",
        "params":  {"proof": proof},
        "id":      1
    }

    r = requests.post(f"http://localhost:8080", json=payload, timeout=30)
    r.raise_for_status()          # raise if HTTP error
    return r.json()               # e.g. {"result": {"score": 1, "messages": []}, "id": 1, "jsonrpc": "2.0"}

if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="/home/t-ilshapiro/CoqStoq/fstarcoq-qwq-32b-singleturn-sft") # path that points to the directory with the model name (e.g. fstarcoq-qwq-32b...)
    parser.add_argument("--sample_n", type=int, default=1) # how many times we sample for each prompt (i.e. sample on same input)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--num_gpus", type=int, default=2)
    args = parser.parse_args()

    print("Starting Coqstoq verification server...")
    # Start the Docker server in detached mode
    
    print("Server is running and ready!")

    # Load validation data
    print("Loading validation data...")
    valid_data = []
    with open("coq-test-data.jsonl") as file:
        for line in file:
            valid_data.append(json.loads(line))
    if args.debug:
        valid_data = valid_data[:100]

    # Load tokenizer and vLLM engine
    print(f"Loading tokenizer and checkpoint from {args.model_name}... ", end="")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    tokenizer.padding_side = "left"
    llm = LLM(model=args.model_name, dtype="bfloat16", max_model_len=16384, tensor_parallel_size=args.num_gpus)

    # Prepare prompts
    print("Preparing prompts...")
    prompts = []
    prompt_to_index = []  # (datum_idx, sample_idx)
    for datum_idx, datum in enumerate(tqdm(valid_data)):
        prompt = datum["user_prompt"]
        if len(tokenizer(prompt).input_ids) > 8192:
            continue
        for sample_idx in range(args.sample_n):
            prompts.append(prompt)
            prompt_to_index.append((datum_idx,sample_idx))

    # Generate with vLLM
    print(f"Sampling responses... {args.sample_n} samples per prompt, temp={args.temperature}")
    sampling_params = SamplingParams(temperature=args.temperature, max_tokens=16384, n=1)
    outputs = llm.generate(prompts, sampling_params)

    # Organize responses into valid_data
    for datum in valid_data:
        datum["model_generated_response"] = [] # length of this list will be sample_n

    for output, (datum_idx, _) in zip(outputs, prompt_to_index):
        response = output.outputs[0].text
        if "<answer>" in response and "</answer>" in response:
            valid_data[datum_idx]["model_generated_response"].append(response) # recall datum_idx is the line number in the jsonl file
    
    # Evaluation
    pass_n_cnt = [0 for _ in range(args.sample_n)]

    results = []
    for datum in tqdm(valid_data):
        id = datum["id"]
        split = datum["split"]
        prompt = datum["user_prompt"]
        pass_flag = False

        for i, response in enumerate(datum["model_generated_response"]):
            answer = response.split("<answer>")[1].split("</answer>")[0]
            result_datum = check_proof(answer)["result"] # check_proof gives e.g. {"result": {"score": 1, "messages": []}, "id": 1, "jsonrpc": "2.0"}
            result, errormsg = bool(result_datum["score"]), result_datum["messages"]
            if result:
                pass_flag = True
            pass_n_cnt[i] += 1 if pass_flag else 0

            if args.debug:
                print("SPLIT", split, "ID:", id)
                print("Prompt:")
                print(prompt)
                print("Model Output:")
                print(response)
                print("Passed?", result)
                if not result:
                    print(errormsg)
                print()
            else:
                results.append({
                    "example_name": datum["name"],
                    "prompt": prompt,
                    "model_output": response,
                    "result": result,
                    "errormsg": errormsg
                })

    print("")
    print("Total data:", len(valid_data))
    print("Pass@n:", [x / len(valid_data) for x in pass_n_cnt])

    if not args.debug:
        with open("coq_valid_test.json", "w") as file:
            json.dump(results, file, indent=4)


    # atexit will stop the container when the script exits
