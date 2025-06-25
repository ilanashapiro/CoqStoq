import re
import json
import os

from trapi import trapi_call

from tqdm import tqdm
from pathlib import Path

PROMPT_REASONING = r"""You are a synthetic data augmentator that generates high-quality instruction data for training a LLM that is fluent in Coq.

Given an instruction and a final code, your task is to generate a chain-of-thought reasoning that an expert might used to generate the code from the instructions.
1. You are NOT simply explaining how the code works, but rather how do you derive the code from the natural language instruction.
2. Include great details how to implement the instructions' requirements in Coq BEFORE the actual Coq code snippet.
This is to make sure that the model trained on this data can properly learn how to condition on the natural language explanations to generate the correct snippet.
    - When writing a lemma or theorem (using `Lemma` or `Theorem`), you should first:
      * Formalize the precise proposition of the theorem that we wish to prove.
      * Specify any required hypotheses and what the theorem guarantees.
      * Outline the proof strategies (tactics) you plan to use.
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
3. Your explanations should be very very detailed like explaining to a beginner, in spoken language style, and do not use bullet lists and hierarchical markdowns. Do not care about the length of your output, you are obliged to produce the most detailed output you can. Just make sure it is very detailed and thorough, as shown in the examples.
Specifically, for each code snippet (theorem, function, proposition/predicate), you MUST write at least 5 sentences of description before each code snippet.

Instruction example:
Given a hash function that takes string of natural numbers `x`, base `base`, prime number `prime`, and indices `i` and `j`. The hash function is already reduced modulo the prime number, i.e. hash(x, base, prime, i, j) = original_hash(x, base, i, j) % prime.
Prove that the hash function is idempotent with respect to the modulus operation, i.e., hash(x, base, prime, i, j) == hash(x, base, prime, i, j) % prime.
Enforce that the prime number is not zero in the Lemma's type signature, and two indices `i` and `j` are such that i <= j <= length of x.

Final code example:
let hash_mod_idem (x:str nat) (base:nat) (prime:nat{{prime <> 0}}) 
    (i:nat) (j:nat {{ i <= j /\\ j <= Seq.length x }})
: Lemma 
  (hash x base prime i j == hash x base prime i j % prime)
= if i = j then ()
  else (
    let lsd = Seq.index x (j - 1) in
    let h = hash x base prime i (j - 1) in
    FStar.Math.Lemmas.lemma_mod_twice (base * h + lsd) prime
  ) 

Chain-of-thought example:
Let's think step-by-step.
We need to write a lemma in F* that proves the idempotence of a hash function with respect to the modulus operation.

First, let's write down the type of the `hash`.
`hash` function takes a string of natural numbers `x`, a base `base`, a prime number `prime`, and two indices `i` and `j`. Note that the prime number is not zero, which should be enforced in the type signature by the restriction syntax {{}}. Also, the indices `i` and `j` are such that `i <= j <= length of x`, which must be also enforced in the type signature.
Therefore, the type of the `hash` function is:
```
let hash (x: str nat) (base: nat) (prime: nat{{prime <> 0}}) (i: nat) (j: nat {{ i <= j /\ j <= Seq.length x }})
```
Knowing this, we can infer the lemma hash_mod_idem's type signature.
```
let hash_mod_idem (x: str nat) (base: nat) (prime: nat{{prime <> 0}})
    (i: nat) (j: nat {{ i <= j /\ j <= Seq.length x }})
: Lemma
```

Let's now investigate the lemma's proof goal.
We need to prove that the hash function is idempotent with respect to the modulus operation, i.e., `hash(x, base, prime, i, j) == hash(x, base, prime, i, j) % prime`.
This can be written as:
```
(hash x base prime i j == hash x base prime i j % prime)
```

Therefore, the overall signature and goal of lemma should be:
```
let hash_mod_idem (x:str nat) (base:nat) (prime:nat{{prime <> 0}}) 
    (i:nat) (j:nat {{ i <= j /\\ j <= Seq.length x }})
: Lemma 
  (hash x base prime i j == hash x base prime i j % prime)
```

Let's construct the proof of this lemma.
For the base case, when `i = j`,
we can simply return `()`, since the hash function is idempotent with respect to the modulus operation.

For the inductive case, when `i < j`, we can use the definition of the hash function.
We can see that the hash function is defined recursively, where the last element is indexed by `j - 1`.
We can use the `Seq.index` function to get the least significant digit of the string at index `j - 1`, and then use the previous hash value `h` from i to j-1 to compute the new hash value.
To complete the induction, we can use the fact that `(n % p) % p == n % p`.
For this purpose, we can use the `FStar.Math.Lemmas.lemma_mod_twice` lemma, which states that if `n` is reduced modulo `p`, then `n % p % p = n % p`.

Instruction:
{instruction}

Final code:
{response}

Chain-of-thought:
"""

# def normalize(X):
#     return X.replace(" ", "").replace("\n", "").replace("*", "").replace("{", "").replace("}", "").replace("\\", "").replace("textbf", "").replace("$", "")

def augment():
    # for FILE in tqdm(os.listdir(SOURCE_DIR)):
    for FILE in [TRAIN_DIR, VALID_DIR]:
        successful_prompt_lists = []
        with open(FILE) as file:
            data = json.load(file)
            # Classify if F* or Pulse

        for datum in data:
            # print(datum.keys())
            # print(datum["base_prompt"][1]["content"])
            # print(datum["completion"][0]["content"])
            instruction = datum["base_prompt"][1]["content"]
            chunk = datum["completion"][0]["content"]
            if "<answer>" in chunk:
                chunk = chunk.split("<answer>")[1].split("</answer>")[0].strip()
            if len(chunk.split("\n")) <= 1:
                continue
            
            # From result and prompt, generate reasoning trace
            response = trapi_call(PROMPT_REASONING.format(language="F*", instruction=instruction, response=chunk))
            if response is None:
                continue
            reasoning = response.strip()
            if reasoning is None:
                continue
            # reasoning = reasoning.group(1).strip()

            print("-------------------------------")
            print("USER:")
            print(instruction)
            print("")
            print("AI:")
            print("<think>")
            print(reasoning)
            print("</think>")
            print("<answer>")
            print(chunk)
            print("</answer>")

            successful_prompt_lists.append({
                "data_source": "pulse_augmented_instruction_collection",
                "prompt": [
                    {
                        "role": "user",
                        "content": instruction,
                    }
                ],
                "ability": "coding/" + "F*",
                "reward_model": {"style": "execution"},
                "extra_info": {
                    "filename": FILE,
                    "question": instruction,
                    "reasoning": reasoning,
                    "answer": chunk,
                    "formatted_response": f"<think>\n{reasoning}\n</think>\n<answer>\n{chunk}\n</answer>"
                },
            })
        
            # with open(TARGET_DIR + f"/{'train' if 'train' in FILE else 'valid'}.jsonl", "w") as file:
            #     for datum in successful_prompt_lists:
            #         file.write(json.dumps(datum, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()