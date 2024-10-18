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
opam switch import switches/eval.opam --switch=coqstoq --repos=default,coq-released=https://coq.inria.fr/opam/released
```

3. Build the CoqStoq repositories 
```
python3 coqstoq/build_projects.py
```

4. Check your setup (from the project root directory)
```
pytest
```



    
