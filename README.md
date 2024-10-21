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
poetry shell
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
