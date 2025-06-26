from __future__ import annotations
from typing import Any, Optional

from pathlib import Path
from dataclasses import dataclass

@dataclass
class Split:
    dir_name: str
    thm_dir_name: str

    @property
    def theorem_list_loc(self) -> Path:
        return Path(f"{self.thm_dir_name}.json")

    def to_json(self) -> Any:
        return {"dir_name": self.dir_name, "thm_dir_name": self.thm_dir_name}

    @classmethod
    def from_json(cls, data: Any) -> Split:
        return cls(data["dir_name"], data["thm_dir_name"])
    
    @classmethod
    def from_name(cls, name: str) -> Split:
        return cls(f"{name}-repos", f"{name}-theorems")


@dataclass
class Project:
    dir_name: str
    split: Split
    commit_hash: Optional[str]
    compile_args: list[str]

    @property
    def workspace(self) -> Path:
        return Path(self.split.dir_name) / self.dir_name

    @property
    def thm_path(self) -> Path:
        return Path(self.split.thm_dir_name) / self.dir_name

    def to_json(self) -> Any:
        return {
            "dir_name": self.dir_name,
            "split": self.split.to_json(),
            "commit_hash": self.commit_hash,
            "compile_args": self.compile_args,
        }

    @classmethod
    def from_json(cls, json_data: Any) -> Project:
        return cls(
            json_data["dir_name"],
            Split.from_json(json_data["split"]),
            json_data["commit_hash"],
            json_data["compile_args"],
        )


TRAIN_SFT_SPLIT = Split("train-sft-repos", "train-sft-theorems")
TRAIN_RL_SPLIT = Split("train-rl-repos", "train-rl-theorems")
VAL_SPLIT = Split("val-repos", "val-theorems")


COMPCERT = Project(
    "compcert",
    TRAIN_RL_SPLIT,
    "6019bc41556473897155259e3d15c5d689185569",
    [
        "-R",
        "lib",
        "compcert.lib",
        "-R",
        "common",
        "compcert.common",
        "-R",
        "x86_64",
        "compcert.x86_64",
        "-R",
        "x86",
        "compcert.x86",
        "-R",
        "backend",
        "compcert.backend",
        "-R",
        "cfrontend",
        "compcert.cfrontend",
        "-R",
        "driver",
        "compcert.driver",
        "-R",
        "export",
        "compcert.export",
        "-R",
        "cparser",
        "compcert.cparser",
        "-R",
        "flocq",
        "Flocq",
        "-R",
        "MenhirLib",
        "MenhirLib",
    ],
)

EXTLIB = Project(
    "ext-lib",
    TRAIN_RL_SPLIT,
    "00d3f4e2a260c7c23d2c0b9cbc69516f8be4ac92",
    ["-Q", "theories", "ExtLib"],
)

FOURCOLOR = Project(
    "fourcolor",
    TRAIN_RL_SPLIT,
    "43719c0fb5fb6cb0c8fc1c2db09efc632c23df90",
    ["-R", "theories", "fourcolor"],
)

MATHCLASSES = Project(
    "math-classes",
    TRAIN_RL_SPLIT,
    "6ad1db9fbd646f8daf1568afef230a76a9f58643",
    ["-R", ".", "MathClasses"],
)

REGLANG = Project(
    "reglang",
    TRAIN_RL_SPLIT,
    "db8be63ec40349e529b6a57c8bcee1acb3f90ceb",
    ["-Q", "theories", "RegLang"],
)

BUCHBERGER = Project(
    "buchberger",
    TRAIN_RL_SPLIT,
    "55ee2e82a05904a7dfb060e558044284abe9c9f5",
    ["-Q", "theories", "Buchberger"],
)

HOARETUT = Project(
    "hoare-tut",
    TRAIN_RL_SPLIT,
    "66dfb255c9e8bb49269d83b3577b285288f39928",
    ["-R", ".", "HoareTut"],
)

ZORNSLEMMA = Project(
    "zorns-lemma",
    TRAIN_RL_SPLIT,
    "aaf46b0c5f7857ce9211cbaaf36f184ca810e0e8",
    ["-R", ".", "ZornsLemma"],
)

HUFFMAN = Project(
    "huffman",
    TRAIN_RL_SPLIT,
    "03d40bd01f2bbccf774e369a3d3feaa2b2a5524a",
    ["-Q", "theories", "Huffman"],
)

POLTAC = Project(
    "poltac",
    TRAIN_RL_SPLIT,
    "90c42be344fd778261fd84b065809b2c81938c49",
    ["-R", ".", "PolTac"],
)

DBLIB = Project(
    "dblib",
    TRAIN_RL_SPLIT,
    "25469872c0ba99b046f7e5b8608205eeea5ac077",
    ["-Q", "src", "Dblib"],
)

ZFC = Project(
    "zfc",
    TRAIN_RL_SPLIT,
    "ede7126560844c381c2b021003a8dbcb0668ecad",
    ["-R", ".", "ZFC"],
)

TRAIN_RL_PROJECTS = [
    COMPCERT,
    EXTLIB,
    FOURCOLOR,
    MATHCLASSES,
    REGLANG,
    BUCHBERGER,
    HOARETUT,
    ZORNSLEMMA,
    HUFFMAN,
    POLTAC,
    DBLIB,
    ZFC,
]


SUDOKU = Project(
    "sudoku",
    TRAIN_SFT_SPLIT,
    "fce3ced21fe5f66d593cf817f70508ba914e8373",
    ["-R", "theories", "Sudoku"],
)

GRAPH_THEORY = Project(
    "graph-theory",
    TRAIN_SFT_SPLIT,
    "4bc29600fd8df75a34f6c0e9c18589c597742a60",
    ["-Q", "theories", "GraphTheory"],
)

QARITH_STERN_BROCOT = Project(
    "qarith-stern-brocot",
    TRAIN_SFT_SPLIT,
    "d3807d3e76a3100e85ba24ef3fe0520f10a7c928",
    ["-R", "theories", "QArithSternBrocot"],
)

COQEAL = Project(
    "coqeal",
    TRAIN_SFT_SPLIT,
    "fb2ecaf4cf99d91351e2a18418d14bea8f24ca60",
    ["-R", ".", "CoqEAL"],
)

TRAIN_SFT_PROJECTS = [
    SUDOKU,
    GRAPH_THEORY,
    QARITH_STERN_BROCOT,
    COQEAL,
]



BERTRAND = Project(
    "bertrand",
    VAL_SPLIT,
    "033b1a8f1a9c121855b6b78cd55154d3c09e1c23",
    ["-Q", "theories", "Bertrand"],
)

STALMARCK = Project(
    "stalmarck",
    VAL_SPLIT,
    "4643e9507e7f03d485fc63410f7f500984d5be8b",
    ["-Q", "theories", "Stalmarck"],
)


VAL_PROJECTS = [
    BERTRAND,
    STALMARCK,
]


PREDEFINED_PROJECTS = TRAIN_RL_PROJECTS + TRAIN_SFT_PROJECTS + VAL_PROJECTS 
