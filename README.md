# CoqStoq
Benchmark and Dataset for Training and Testing Coq proof search tools.  

## Using the benchmark  
- This dataset is intended to be used via docker.  
- To see how to use this dataset outside of docker, simply reference the [Dockerfile](Dockerfile)

### Cloning the repository
```
git clone -b deepproof-full https://github.com/rkthomps/CoqStoq --recurse-submodules
```

### Building the docker image
Please allow for 1-2 hours to build the image.
```
cd CoqStoq
docker build -t coqstoq-full .
```

### Running commands
1. Run the tests:
```
docker run coqstoq-full poetry run pytest
```

2. Use the api to get examples:
```
Get the available splits:
===========================
docker run coqstoq-full poetry run python3 api.py get_splits

Expected output:
{
  "splits": [
    "train-sft",
    "train-rl",
    "val",
    "cutoff",
    "test",
  ]
}


Get the number of examples in a split:
========================================
docker run coqstoq-full poetry run python3 api.py get_num_theorems train-rl

Expected output:
{
  "num_theorems": 80274 
}


Get the relevant information about an example:
docker run coqstoq-full poetry run python3 api.py get_theorem_info train-sft 3001 

Expected output:
{
  "split": "train-rl",
  "index": 3001,
  "prefix": ...  # the portion of the file comming before the theorem
  "suffix": ...  # the portion of the file comming after the proof 
  "theorem": ... # the theorem statement
  "groud_truth": ... # the human-written proof
}


Get the relevant information about a range of examples:
docker run coqstoq-full poetry run python3 api.py get_theorem_range train-sft 3 5 

Expected output:
[
  {
    "split": "train-rl",
    "index": 3,
    "prefix": ...,
    "suffix": ...,
    "theorem": ...,
    "ground_truth": ...,
  },
  {
    "split": "train-rl",
    "index": 4,
    "prefix": ...,
    "suffix": ...,
    "theorem": ...,
    "ground_truth": ...,
  },
]



```

3. Run the verification server: \
   Starting the server:
```
# "train-rl" is the split where checking is happening
# 1 is the theorem index in the split

docker run -p 8080:8080 coqstoq-full poetry run python3 coqstoq/checker_server/server.py train-rl 77785 . 
```

  
  Sending requests:
```
# A successful request:

curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "check_proof",
    "params": {"proof": "Proof. intros. rewrite -> plus_O_n. reflexivity."},
    "id": 1
  }'

# Expected result:
{"result": {"score": 1, "messages": []}, "id": 1, "jsonrpc": "2.0"}

An unsuccessful request:
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "check_proof",
    "params": {"proof": "Proof. simpl. Qed."},
    "id": 1
  }'

# Expected result:
{"result": {"score": 0, "messages": [" (in proof trivial_three): Attempt to save an incomplete proof", " (in proof trivial_three): Attempt to save an incomplete proof"]}, "id": 1, "jsonrpc": "2.0"}
```
