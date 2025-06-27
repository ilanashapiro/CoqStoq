import os
import json
from pathlib import Path
import subprocess
from coqstoq.build.project import Project
from coqstoq.index_thms.eval_thms import compile_file
from coqstoq.create_theorem_lists import TheoremReference, load_reference_list
from coqstoq.build.project import (
    PREDEFINED_PROJECTS,
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
    SUDOKU,
    BERTRAND,
    GRAPH_THEORY,
    STALMARCK,
    QARITH_STERN_BROCOT,
    COQEAL,
    VAL_SPLIT,
)

import logging


def test_select_files_compile():
    """
    Tests that select files from each project compile in
    the current environment.
    """
    test_pairs: list[tuple[Project, Path]] = [
        (COMPCERT, Path("backend/Asmgenproof0.v")),
        (EXTLIB, Path("theories/Data/Set/TwoThreeTrees.v")),
        (FOURCOLOR, Path("theories/fourcolor.v")),
        (MATHCLASSES, Path("interfaces/rationals.v")),
        (REGLANG, Path("theories/wmso.v")),
        (BUCHBERGER, Path("theories/WfR0.v")),
        (HOARETUT, Path("exgcd.v")),
        (ZORNSLEMMA, Path("ZornsLemma.v")),
        (HUFFMAN, Path("theories/Huffman.v")),
        (POLTAC, Path("ZSignTac.v")),
        (DBLIB, Path("src/Environments.v")),
        (ZFC, Path("Russell.v")),
        (SUDOKU, Path("theories/Sudoku.v")),
        (BERTRAND, Path("theories/Summation.v")),
        (GRAPH_THEORY, Path("theories/planar/K4plane.v")),
        (STALMARCK, Path("theories/Algorithm/refl.v")),
        (QARITH_STERN_BROCOT, Path("theories/Zaux.v")),
        (COQEAL, Path("refinements/multipoly.v")),
    ]

    for p, f in test_pairs:
        logging.info(f"Compiling {p.workspace / f}")
        compile_file(p, p.workspace / f, timeout=None)

