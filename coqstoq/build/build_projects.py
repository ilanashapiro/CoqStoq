import math
import argparse
import subprocess
from pathlib import Path
from dataclasses import dataclass
from coqstoq.build.project import (
    COMPCERT,
    PNVROCQLIB,
    BB5,
    PREDEFINED_PROJECTS,
    Project
)
import logging
import multiprocessing as mp

logger = logging.getLogger(__name__)

N_JOBS_PER_BUILD = 8

@dataclass
class BuildInstructions:
    project: Project
    instrs: list[list[str]]


def routine_build(project: Project) -> BuildInstructions:
    return BuildInstructions(
        project,
        [["make", "-j", str(N_JOBS_PER_BUILD)]],
    )

def pnv_build() -> BuildInstructions:
    coq_makefile = ["coq_makefile", "-f", "_CoqProject", "-o", "Makefile.coq"]
    make = ["make", "-f", "Makefile.coq", "-j", str(N_JOBS_PER_BUILD)]
    return BuildInstructions(
        PNVROCQLIB,
        instrs=[coq_makefile, make],
    )


def compcert_build() -> BuildInstructions:
    configure = ["./configure", "x86_64-linux"]
    make_depend = ["make", "depend", "-j", str(N_JOBS_PER_BUILD)]
    make_proof = ["make", "proof", "-j", str(N_JOBS_PER_BUILD)]
    return BuildInstructions(
        COMPCERT,
        instrs=[configure, make_depend, make_proof],
    )


# Removed BB52 theorem.v; BB42 theorem.v; and BB25 theorem.v
MODIFIED_BB5_CP = """\
-Q . BusyCoq
BB52Statement.v
BB52.v
Finned1.v
Finned3.v
Finned5.v
FixedBin.v
Helper.v
Individual.v
Permute.v
ShiftOverflow.v
Skelet15.v
Skelet1.v
Skelet33.v
Skelet35.v
Compute.v
Finned2.v
Finned4.v
Finned.v
Flip.v
Individual52.v
LibTactics.v
ShiftOverflowBins.v
Skelet10.v
Skelet17.v
Skelet26.v
Skelet34.v
TM.v
"""

def bb5_build() -> BuildInstructions:
    with open(BB5.workspace / "_Custom_CoqProject", "w") as fout:
        fout.write(MODIFIED_BB5_CP)
    instrs = [
        ["coq_makefile", "-f", "_Custom_CoqProject", "-o", "CustomMakefile.coq"],
        ["make", "-f", "CustomMakefile.coq", "-j", str(N_JOBS_PER_BUILD)],
    ]
    return BuildInstructions(BB5, instrs)



def run_build(instructions: BuildInstructions):
    logger.info(f"Building {instructions.project.dir_name}")
    for instr in instructions.instrs:
        result = subprocess.run(
            instr, cwd=instructions.project.workspace.resolve(), capture_output=True
        )
        if result.returncode != 0:
            msg = f"Failed to build {instructions.project.dir_name}. To debug, run: {instr}."
            logger.warning(msg)
            return
    logger.info(f"Successfully built {instructions.project.dir_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Build CoqStoq projects on your machine.")
    default_num_jobs = math.ceil(mp.cpu_count() / N_JOBS_PER_BUILD)
    parser.add_argument("--n_jobs", type=int, default=default_num_jobs)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    all_build_instrs: list[BuildInstructions] = []
    for p in PREDEFINED_PROJECTS:
        if p == COMPCERT:
            all_build_instrs.append(compcert_build())
        elif p == PNVROCQLIB:
            all_build_instrs.append(pnv_build())
        elif p == BB5:
            all_build_instrs.append(bb5_build())
        else:
            all_build_instrs.append(routine_build(p))

    with mp.Pool(args.n_jobs) as pool:
        pool.map(run_build, all_build_instrs)
