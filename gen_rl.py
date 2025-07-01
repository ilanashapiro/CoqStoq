import json, sys, time, subprocess
from pathlib import Path
from gen_sft import combine_to_jsonl

USER_PROMPT_FORMAT = """The theorem I'm trying to prove is \n```\n{theorem}\n```\n#####\n\nThe file context in which I'm writing the proof is \n```\n{file_context}\n```\n#####\n\nStart the proof with the following tactic:\n```\nProof\n```\n\n"""

SAVE_LOC = Path("rl-data")
SAVE_LOC.mkdir(parents=True, exist_ok=True)
OUT_PATH_JSONL = SAVE_LOC.with_suffix(".jsonl")

SPLIT = "train-rl"
NUM_EXAMPLES = 80274
START_INDEX = sum(1 for f in SAVE_LOC.iterdir() if f.is_file())

def augment():
    print(f"Starting RL augmentation from index {START_INDEX} for {NUM_EXAMPLES} examples.")
    augmented_count = 0

    theorem_info_list = subprocess.run(
        ["docker", "run", "coqstoq-full", "poetry", "run", "python3", "api.py", "get_theorem_range", "train-rl", str(START_INDEX), str(NUM_EXAMPLES)],
        capture_output=True,
        text=True
    )
    theorem_info_list = json.loads(str(theorem_info_list.stdout))["theorems"]

    for thrm_info in theorem_info_list:
        user_prompt = USER_PROMPT_FORMAT.format(theorem=thrm_info["theorem"], file_context=thrm_info["prefix"])
        entry = {
            "user_prompt": user_prompt,
            "split":  thrm_info["split"],
            "index":  thrm_info["index"],
            "ground_truth": thrm_info["ground_truth"],
        }

        # ──────────────────────────────────────────────────────────────
        # Write ONE file per example
        #   e.g.  rl-data/train-rl_226.json
        # ──────────────────────────────────────────────────────────────
        out_path = SAVE_LOC / f"{thrm_info['split']}_{thrm_info['index']}.json"
        with open(out_path, "w", encoding="utf-8") as f_out:
            json.dump(entry, f_out, ensure_ascii=False, indent=2)

        augmented_count += 1
        print(f"{augmented_count+START_INDEX}/{NUM_EXAMPLES} done  ->  {SAVE_LOC}", file=sys.stderr)

    print(f"Wrote {augmented_count} per-example files to “{SAVE_LOC}”.")
    
if __name__ == "__main__":
    # augment()
    combine_to_jsonl(SAVE_LOC, OUT_PATH_JSONL)