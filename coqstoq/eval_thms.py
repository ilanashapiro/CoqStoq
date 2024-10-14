from __future__ import annotations
import os
import argparse
import hashlib
from typing import Optional, Any
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import subprocess

from coqpyt.coq.structs import TermType, Step
from coqpyt.coq.base_file import CoqFile
from coqstoq.compile_args import COMPCERT_ARGS, EXTLIB_ARGS, FOURCOLOR_ARGS


class Split(Enum):
    VAL = 1
    TEST = 2

    @property
    def repo_dir_name(self) -> str:
        match self:
            case Split.VAL:
                return "val-repos"
            case Split.TEST:
                return "test-repos"

    @property
    def thm_dir_name(self) -> str:
        match self:
            case Split.VAL:
                return "val-theorems"
            case Split.TEST:
                return "test-theorems"


class Project(Enum):
    COMPCERT = "compcert"
    EXTLIB = "ext-lib"
    FOURCOLOR = "fourcolor"

    @property
    def dir_name(self) -> str:
        return self.value

    @property
    def split(self) -> Split:
        match self:
            case Project.COMPCERT:
                return Split.TEST
            case Project.EXTLIB:
                return Split.TEST
            case Project.FOURCOLOR:
                return Split.TEST

    @property
    def workspace(self) -> Path:
        return Path(self.split.repo_dir_name) / self.dir_name

    @property
    def compile_args(self) -> list[str]:
        match self:
            case Project.COMPCERT:
                return COMPCERT_ARGS
            case Project.EXTLIB:
                return EXTLIB_ARGS
            case Project.FOURCOLOR:
                return FOURCOLOR_ARGS


@dataclass
class Position:
    line: int
    column: int

    def to_json(self) -> Any:
        return {"line": self.line, "column": self.column}

    @classmethod
    def from_json(cls, data: Any) -> Position:
        return cls(data["line"], data["column"])


@dataclass
class TestTheorem:
    project: Project
    path: Path  # relative path in the project
    start_pos: Position  # inclusive
    end_pos: Position  # inclusive line, exclusive column
    hash: str  # Hash of file when theorem was collected

    def to_json(self) -> Any:
        return {
            "project": self.project.value,
            "path": str(self.path),
            "start_pos": self.start_pos.to_json(),
            "end_pos": self.end_pos.to_json(),
            "hash": self.hash,
        }

    @classmethod
    def from_json(cls, data: Any) -> TestTheorem:
        return cls(
            Project(data["project"]),
            Path(data["path"]),
            Position.from_json(data["start_pos"]),
            Position.from_json(data["end_pos"]),
            data["hash"],
        )


def is_eval_theorem(termtype: TermType) -> bool:
    match termtype:
        case (
            TermType.THEOREM
            | TermType.LEMMA
            | TermType.FACT
            | TermType.REMARK
            | TermType.COROLLARY
            | TermType.PROPOSITION
            | TermType.PROPERTY
        ):
            return True
        case _:
            return False


def is_end_proof(coq_file: CoqFile, step: Step) -> bool:
    return coq_file.context.expr(step)[0] in ["VernacEndProof", "VernacExactProof"]


def extract_proof(coq_file: CoqFile) -> list[Step]:
    assert is_eval_theorem(coq_file.context.term_type(coq_file.curr_step))
    assert not is_end_proof(coq_file, coq_file.curr_step)
    proof_steps: list[Step] = []
    while not is_end_proof(coq_file, coq_file.curr_step):
        coq_file.exec()
        proof_steps.append(coq_file.curr_step)
        if coq_file.steps_taken >= len(coq_file.steps):
            raise ValueError("Proof never ended.")
    start_pos = proof_steps[0].ast.range.start
    end_pos = proof_steps[-1].ast.range.end
    return proof_steps


def ends_with_qed(proof: list[Step]) -> bool:
    assert 0 < len(proof)
    return proof[-1].text.strip().endswith("Qed.")


def get_file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


def get_test_thm(project: Project, path: Path, steps: list[Step]) -> TestTheorem:
    assert 0 < len(steps)
    lsp_start = steps[0].ast.range.start
    lsp_end = steps[-1].ast.range.end
    assert path.resolve().is_relative_to(project.workspace.resolve())
    rel_path = path.relative_to(project.workspace)
    return TestTheorem(
        project,
        rel_path,
        Position(lsp_start.line, lsp_start.character),
        Position(lsp_end.line, lsp_end.character),
        get_file_hash(path),
    )


class CoqComplieError(Exception):
    pass


def compile_file(project: Project, path: Path):
    project_loc = project.workspace
    assert project_loc.exists()
    cur_dir = Path.cwd().resolve()
    full_path = path.resolve()
    os.chdir(project_loc)
    tmp_out_loc = Path(path.with_suffix(".vo").name)
    try:
        out = subprocess.run(
            ["coqc", "-o", tmp_out_loc, *project.compile_args, full_path],
            capture_output=True,
        )
        if out.returncode == 0:
            return None
        else:
            raise CoqComplieError(out.stderr)
    finally:
        if tmp_out_loc.exists():
            os.remove(tmp_out_loc)
        os.chdir(cur_dir)


def find_eval_theorems(project: Project, path: Path) -> list[TestTheorem]:
    compile_file(project, path)
    str_file_path = str(path.resolve())
    str_workspace_path = str(project.workspace.resolve())
    proofs: list[TestTheorem] = []
    with CoqFile(str_file_path, workspace=str_workspace_path) as coq_file:
        while coq_file.steps_taken < len(coq_file.steps):
            tt = coq_file.context.term_type(coq_file.curr_step)
            if is_eval_theorem(tt):
                steps = extract_proof(coq_file)
                assert 0 < len(steps)
                if ends_with_qed(steps):
                    test_thm = get_test_thm(project, path, steps)
                    proofs.append(test_thm)
                    print("".join([s.text for s in steps]))
            else:
                coq_file.exec()
    return proofs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Project, choices=list(Project))
    parser.add_argument("path", type=Path)

    args = parser.parse_args()

    # compile_file(args.path, args.project)
    find_eval_theorems(args.project, args.path)
