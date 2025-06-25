# CoqStoq
Benchmark for evaluating Coq proof search tools.

## Installation
**Requirements**:
- opam >= 2.1.2 (previous versions are untested)
- poetry >= 1.8.3 (previous versions are untested) 
- python >= 3.11 (previous versions are untested)

1. Clone this repository and its submodules:
```
git clone git@github.com:rkthomps/CoqStoq --recurse-submodules
```

2. Build and initialize the CoqStoq python environment:
```
cd CoqStoq
poetry install
eval $(poetry env activate)
```

2. Install the CoqStoq opam switch
```
opam switch import coqstoq.opam --switch=coqstoq --repos=default,coq-released=https://coq.inria.fr/opam/released
```

3. Build the CoqStoq repositories 
```
python3 coqstoq/build_projects.py
```

4. Check your setup (from the project root directory)
```
pytest
```

## Checking Server
### Starting the server
Start the checking server by running the following command:
```
python3 coqstoq/checker_server/server.py test 0 /home/ubuntu/CoqStoq
```
Note that 
- "test" is the name of the split where the example lives. 
  Other splits include "val" and "cutoff" (train coming shortly.)
- 0 is the index of hte example in the split
- "/home/ubuntu/CoqStoq" is the path to this repository.

### Calling the server
Simply call the server with a proof. 
For example:
```
curl -X POST http://localhost:8080 \   
  -H "Content-Type: application/json" \
  -d '{
      "jsonrpc": "2.0",
      "method": "check_proof",
      "params": {"proof": "Proof. reflexivity. Qed."},
      "id": 1
    }'
```

If the proof is correct, the server will return an object like the following:
```
{"result": {"score": 1, "messages": []}, "id": 1, "jsonrpc": "2.0"}
```

If the proof is incorrect, the server will return an object like the following:
```
{'result': {'score': 0,
  'messages': [' The relation Real.le is not a declared reflexive relation. Maybe you need to require the Coq.Classes.RelationClasses library',
   ' (in proof eqR_le): Attempt to save an incomplete proof',
   ' The relation Real.le is not a declared reflexive relation. Maybe you need to require the Coq.Classes.RelationClasses library',
   ' (in proof eqR_le): Attempt to save an incomplete proof']},
 'id': 1,
 'jsonrpc': '2.0'}
```


## Usage
### `EvalThm`
A eval theorem is represented by the following python object:
```
@dataclass
class EvalTheorem:
    project: Project
    path: Path  # relative path in the project
    theorem_start_pos: Position  # inclusive
    theorem_end_pos: Position  # inclusive line, exclusive column
    proof_start_pos: Position  # inclusive
    proof_end_pos: Position  # inclusive line, exclusive column
    hash: str  # Hash of file when theorem was collected
```

### Loading `EvalThm`s from a Split
You can interact with the predefined `EvalThm`s in CoqStoq in the following way.
Note that CoqStoq's theorems have been shuffled. That is, for some index $i$, the theorem at that index is determined completely randomly. This means, for example, that taking a slice of the first 500 theorems is a random sample of theorems from the particular split. 

Also note, if you are going to load many theorems from CoqStoq, it is more efficient to use the `get_theorems` function than the `get_theorem` function. 
```
from coqstoq import num_theorems, get_theorem, get_theorem_list, Split

# number of theorems in the testing split
print(num_theorems(Split.TEST)) 

# get the theorem at index 10 from the validation split
print(get_theorem(Split.VAL), 10) 

# get the list of theorems in the cutoff split 
print(get_theorems(Split.CUTOFF)) 
``` 

### Reporting Results
To add the results of a new tool to CoqStoq, we ask that the results of your tool be presented in a `.json` file containing the following data structure (which has a `.to_json()`) 
```
@dataclass
class EvalResults:
    hardware: str  # Description of hardware used
    results: list[Result]
```

```
@dataclass
class Result:
    thm: EvalTheorem
    proof: Optional[str]  # Proof found
    time: Optional[float]  # Time in seconds
```

### Adding Projects
Suppose you want to add two projects, "bar" and "baz" to CoqStoq.
- First, create a new split. 
  Suppose you want to call your split "foo".
  - Place the projects "bar" and "baz" under "foo-repos/bar" and "foo-repos/baz" respectively.
  - Complie the projects. 
    Note that if you change the opam switch from the coqstoq opam switch, some of the tests may not pass. 
    That is fine if you only care about your new projects.
- Second, you must create a a "configuration" for your custom split that tells CoqStoq how to compile each file in each project.   
  For example, I would create a config `foo.yaml` as follows
  ```yaml
  bar:
    compile_args:
      - -Q
      - .
      - Bar

  baz:
    compile_args:
      - Q
      - .
      - Baz
  ```
- Third, you must find the theorems to evaluate on. You can do this by running
  ```bash
  python3 coqstoq/find_eval_thms.py --custom-split-name foo
  ```
- Fourth, you must shuffle the split. You can do this as follows: 
  ```bash
   python3 coqstoq/create_theorem_lists.py foo
   ```


  


## Limitations
1. We impose a 2-minute timeout when compiling files with `coqc`, if a file takes longer than 2 minutes to compile it is not included in our evaluation. In practice, this only affects 4 files from the `BB5` project in the cutoff split. Namely, `BB42Theorem.v, BB52Theorem.v, BB24Theorem.v, Skelet1.v`.
2. CoqStoq depends on coq-lsp to parse Coq Files. Sometimes, `coq-lsp` fails unexpectedly even when `coqc` successfully compiled a file. In our case, `coq-lsp` failed on 49 files from the fourcolor project where all of the files were of the form `theories/job<n1>to<n2>.v`. Each of these files contain a single proof that is one tactic long: `Proof. CheckReducible. Qed`. 
