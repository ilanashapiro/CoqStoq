import json, sys, time, subprocess

from trapi_DO_NOT_COMMIT import trapi_call
sys.path.append("CoqStoq")

from pathlib import Path
from azure.core.exceptions import ServiceResponseError, HttpResponseError

def get_prompt_reasoning(language, instruction, response): 
    return f"""You are a synthetic data augmentator that generates high-quality instruction data for training a LLM that is fluent in {language}.

    Given an instruction and a final code, your task is to generate a chain-of-thought reasoning that an expert might used to generate the code from the instructions.
    1. You are NOT simply explaining how the code works, but rather how do you derive the code from the natural language instruction.
    2. Include great details how to implement the instructions' requirements in {language} BEFORE the actual {language} code snippet.
    This is to make sure that the model trained on this data can properly learn how to condition on the natural language explanations to generate the correct snippet.
        - When writing a lemma or theorem (using `Lemma` or `Theorem`), you should first:
        * Examine the type signature of the lemma or theorem.
        * Identify the main goal of the lemma or theorem.
        * Describe the mathematical or logical properties that the lemma or theorem is asserting.
        * Discuss any assumptions or hypotheses that are necessary for the proof.
        * Outline the proof strategy, including the tactics you plan to use.
        Only after this should you write the proof script.

    - When writing a proposition or predicate (e.g., `Definition` with a `Prop` type), you should first:
        * Formalize the properties being checked.
        * Specify the type of the proposition.
        * State any type restrictions or constraints explicitly (using dependent types or curly braces for arguments).
        Then provide the proposition definition.

    - When writing a function (using `Definition` or `Fixpoint` returning `Set`, `Type`, or `bool`, etc.), you should first:
        * Formalize the function's type signature.
        * Describe the high-level functionality.
        * Provide the detailed algorithmic implementation.
        * Explain how the implementation meets the specification.
        After this explanation, include the actual function code.

    3. Your explanations should be very very detailed like explaining to a beginner, in spoken language style, and do not use bullet lists and hierarchical markdowns. Do not care about the length of your output, you are obliged to produce the most detailed output you can. Just make sure it is very detailed and thorough, as shown in the examples. Specifically, for each code snippet (theorem, function, proposition/predicate), you MUST write at least 5 sentences of description before each code snippet.

    4. However, your explanations should not be too verbose, and should not include any unnecessary information. Do not repeat the same information multiple times, and do not include any irrelevant information. The explanations should be concise and to the point, while still being detailed enough to understand the code. Try to keep your reasoning under approximately {len(response)} words.
    
    5. Remembers, ALL of the details about how to implement the instructions' requirements in {language} need to come BEFORE the actual {language} code snippet. There should be no additional explanations after the code snippet, except for the final summary of the proof or function.

    Instruction example:
    Given a hash function that takes string of natural numbers `x`, base `base`, prime number `prime`, and indices `i` and `j`. The hash function is already reduced modulo the prime number, i.e. hash(x, base, prime, i, j) = original_hash(x, base, i, j) % prime.
    Prove that the hash function is idempotent with respect to the modulus operation, i.e., hash(x, base, prime, i, j) == hash(x, base, prime, i, j) % prime.
    Enforce that the prime number is not zero in the Lemma's type signature, and two indices `i` and `j` are such that i <= j <= length of x.

    Final code example:
    From {language} Require Import List Arith.PeanoNat.
    Import ListNotations.

    (* A “mathematical” polynomial hash that does **not** reduce modulo [prime]. *)
    Parameter original_hash :
    list nat ->            (* the input sequence x          *)
    nat ->                 (* the base                      *)
    nat -> nat -> nat.     (* indices i  j                  *)

    (* The concrete hash carries out the reduction right away. *)
    Definition hash
            (x     : list nat)
            (base  : nat)
            (prime : nat)
            (i j   : nat) : nat :=
    original_hash x base i j mod prime.
    
    Lemma hash_mod_idem :
    forall (x : list nat) (base prime i j : nat),
        prime <> 0               ->           (* non-zero prime                *)
        i <= j                   ->           (* slice bounds—as requested     *)
        j <= length x            ->
        hash x base prime i j mod prime =
        hash x base prime i j.
    Proof.
    intros x base prime i j Hprime _ _.           (* keep side conditions    *)
    unfold hash.                                  (* expose the outer [mod]  *)
    rewrite Nat.mod_mod by exact Hprime.          (* (a mod p) mod p = …     *)
    reflexivity.
    Qed.

    Chain-of-thought example:
    Let's think step-by-step.
    We need to write a lemma in {language} that proves the idempotence of a hash function with respect to the modulus operation.

    First, let's write down the definition of the `hash` function.
    `hash` function takes a string of natural numbers `x`, a base `base`, a prime number `prime`, and two indices `i` and `j`. `hash` function must be fully reduced modulo prime. In Coq, we cannot reference `hash` in its own definition, so we will define a helper function `original_hash` that computes the hash without reduction modulo prime.
    The `original_hash` function takes the same parameters as `hash`, but it does not reduce the result modulo prime. It computes the hash value based on the input string `x`, the base `base`, and the indices `i` and `j`.
    We can define `original_hash` as a parameter, which will be provided by the user.
    In Coq, we can define `original_hash` as follows:
    ```
    Parameter original_hash :
    list nat ->            (* the input sequence x          *)
    nat ->                 (* the base                      *)
    nat -> nat -> nat.     (* indices i  j                  *)
    ```
    This means that `original_hash` is a function that takes a list of natural numbers, a base, and two indices, and returns a natural number.
    Next, we can define the `hash` function using `original_hash`. The `hash` function will compute the hash value by calling `original_hash` and then reducing the result modulo prime.
    In Coq, we can define `hash` as follows:
    ```
    Definition hash
            (x     : list nat)
            (base  : nat)
            (prime : nat)
            (i j   : nat) : nat :=
    original_hash x base i j mod prime.                                                                         
    ```
    This means that `hash` is a function that takes a list of natural numbers, a base, a prime number, and two indices, and returns a natural number that is the result of `original_hash x base i j` reduced modulo `prime`.

    Now, we have the `hash` function defined. The next step is to prove that the hash function is idempotent with respect to the modulus operation, i.e., `hash(x, base, prime, i, j) == hash(x, base, prime, i, j) % prime`.

    To do this, we need to write a lemma that states that the hash function is idempotent with respect to the modulus operation. Note that the prime number is not zero, which should be enforced in the type signature by the restriction syntax <>. Also, the indices `i` and `j` are such that `i <= j <= length of x`, which must be also enforced in the type signature. Knowing this, we can infer the lemma hash_mod_idem's type signature and proof goal as follows:
    ```
    Lemma hash_mod_idem :
    forall (x : list nat) (base prime i j : nat),
        prime <> 0               ->           (* non-zero prime                *)
        i <= j                   ->           (* slice bounds—as requested     *)
        j <= length x            ->
        
    ```
    Let's now investigate the lemma's proof goal.
    We need to prove that the hash function is idempotent with respect to the modulus operation, i.e., `hash(x, base, prime, i, j) == hash(x, base, prime, i, j) % prime`.
    This can be written as:
    ```           
    hash x base prime i j mod prime =
        hash x base prime i j.
    ```

    Therefore, the overall signature and goal of lemma should be:
    ```
    Lemma hash_mod_idem :
    forall (x : list nat) (base prime i j : nat),
        prime <> 0               ->           
        i <= j                   ->           
        j <= length x            ->
        hash x base prime i j mod prime =
        hash x base prime i j.
    ```

    Let's construct the proof of this lemma. The goal currently is: 
    ```(hash x base prime i j) mod prime = hash x base prime i j```

    First, let's bring assumptions and universally quantified variables from the goal into the proof context using the `intros` tactic. This will allow us to use them in the proof as follows:
    ```
    intros x base prime i j Hprime _ _.
    ```

    After this, the proof context will contain the variables `x`, `base`, `prime`, `i`, and `j`, as well as the assumptions `Hprime` (that prime is not zero) and the inequalities `i <= j` and `j <= length x`.
    Next, we need to unfold the definition of `hash` to expose the outer modulus operation.
    We can do this using the `unfold` tactic as follows:
    ```
    unfold hash.
    ```

    After unfolding, the goal will look like this:
    ```(original_hash x base i j) mod prime = (original_hash x base i j) mod prime```

    Now, we can use the `rewrite` tactic to simplify the goal. We can rewrite the goal using the lemma `Nat.mod_mod`, which states that `(a mod p) mod p = a mod p` for any natural number `a` and prime `p`. We can apply this lemma by providing the assumption `Hprime` that `prime` is not zero:
    ```rewrite Nat.mod_mod by exact Hprime.```

    After this rewrite, the goal will become:
    ```(original_hash x base i j) mod prime = (original_hash x base i j) mod prime```

    Finally, we can conclude the proof by using the `reflexivity`
    tactic, which states that both sides of the equation are equal:
    ```reflexivity.```      

    We conclude our proof with the QED command:
    ```
    Qed.
    ```

    Instruction:
    {instruction}

    Final code:
    {response}

    Chain-of-thought:
    """

MAX_RETRIES = 3          # how many times to retry the call
BACKOFF     = 5          # seconds to wait between retries
USER_PROMPT_FORMAT = """The theorem I'm trying to prove is \n```\n{theorem}\n```\n#####\n\nThe file context in which I'm writing the proof is \n```\n{file_context}\n```\n#####\n\nStart the proof with the following tactic:\n```\nProof\n```\n\n"""

SAVE_LOC = Path("sft-data")
SAVE_LOC.mkdir(parents=True, exist_ok=True)
OUT_PATH_JSONL = SAVE_LOC.with_suffix(".jsonl")

SPLIT = "train-sft"
NUM_EXAMPLES = 9410 
START_INDEX = sum(1 for f in SAVE_LOC.iterdir() if f.is_file())

def combine_to_jsonl(src_dir: Path, out_file: Path) -> None:
    """
    Read every *.json file in `src_dir` and append its (single) JSON object
    as one line to `out_file` in JSON‑Lines format.
    Existing output is overwritten.
    """
    with out_file.open("w", encoding="utf-8") as fout:
        # sort() gives stable order; drop if you don’t care
        for fp in sorted(src_dir.glob("*.json")):
            with fp.open("r", encoding="utf-8") as fin:
                obj = json.load(fin)          # each file contains ONE object
            json.dump(obj, fout, ensure_ascii=False)
            fout.write("\n")                  # newline separates entries
    print(f"Wrote {out_file} with {len(list(src_dir.glob('*.json')))} lines.")

def safe_trapi_call(prompt: str):
    """
    Wrapper around trapi_call that retries a few times and returns None
    if it still fails.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return trapi_call(prompt)
        except (ServiceResponseError, HttpResponseError) as e:
            print(f"[trapi_call] attempt {attempt}/{MAX_RETRIES} failed: {e}",
                  file=sys.stderr)
            if attempt == MAX_RETRIES:
                # give up after last attempt
                return None
            time.sleep(BACKOFF)      # simple linear back-off (or use 2**attempt)
        except Exception as e:
            # Catch-all so one unexpected error doesn't crash you
            print(f"[trapi_call] unexpected error: {e}", file=sys.stderr)
            return None

def augment():
    print(f"Starting SFT augmentation from index {START_INDEX} for {NUM_EXAMPLES} examples.")
    augmented_count = 0

    theorem_info_list = subprocess.run(
        ["docker", "run", "coqstoq-full", "poetry", "run", "python3", "api.py", "get_theorem_range", "train-sft", str(START_INDEX), str(NUM_EXAMPLES)],
        capture_output=True,
        text=True
    )
    theorem_info_list = json.loads(str(theorem_info_list.stdout))["theorems"]

    for thrm_info in theorem_info_list:
        user_prompt = USER_PROMPT_FORMAT.format(theorem=thrm_info["theorem"], file_context=thrm_info["prefix"])
        proof       = thrm_info["ground_truth"]
        prompt      = get_prompt_reasoning(language="Coq",
                                    instruction=user_prompt,
                                    response=proof)

        response  = safe_trapi_call(prompt)
        if not response:
            print(f"[augment] Failed to get response for theorem {thrm_info['index']} in split {thrm_info['split']}. Skipping.", file=sys.stderr)
            continue

        reasoning = response.strip()
        if not reasoning:
            print(f"[augment] Empty reasoning for theorem {thrm_info['index']} in split {thrm_info['split']}. Skipping.", file=sys.stderr)
            continue

        entry = {
            "data_source": "CoqStoq",
            "prompt": [{"role": "user", "content": user_prompt}],
            "ability": "coding/Coq",
            "reward_model": {"style": "execution"},
            "extra_info": {
                "question":          user_prompt,
                "reasoning":         reasoning,
                "answer":            proof,
                "formatted_response": (
                    f"<think>\n{reasoning}\n</think>\n"
                    f"<answer>\n{proof}\n</answer>"
                ),
                "split":  thrm_info["split"],
                "index":  thrm_info["index"],
            },
        }

        # ──────────────────────────────────────────────────────────────
        # Write ONE file per example
        #   e.g.  sft-data/train-sft_226.json
        # ──────────────────────────────────────────────────────────────
        out_path = SAVE_LOC / f"{thrm_info['split']}_{thrm_info['index']}.json"
        with open(out_path, "w", encoding="utf-8") as f_out:
            json.dump(entry, f_out, ensure_ascii=False, indent=2)

        augmented_count += 1
        print(f"{augmented_count+START_INDEX}/{NUM_EXAMPLES} done  ->  {SAVE_LOC}", file=sys.stderr)

    print(f"Wrote {augmented_count} files to “{SAVE_LOC}”.")
    
if __name__ == "__main__":
    # augment()
    combine_to_jsonl(SAVE_LOC, OUT_PATH_JSONL)