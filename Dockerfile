FROM ubuntu:22.04

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y build-essential
RUN apt-get install -y software-properties-common

ENV DEBIAN_FRONTEND=noninteractive

RUN apt install -y git
RUN apt install -y opam
RUN opam -y init

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install -y python3.12-dev
RUN apt install -y python3.12-venv

WORKDIR /app

COPY ./coqstoq.opam /app/coqstoq.opam

RUN apt-get install -y libgmp-dev pkg-config
RUN opam switch import -y coqstoq.opam --switch=coqstoq --repos=default,coq-released=https://coq.inria.fr/opam/released
RUN opam switch set coqstoq

# Equivalent to `eval $(opam env)`
ENV OPAM_SWITCH_PREFIX='/root/.opam/coqstoq'
ENV CAML_LD_LIBRARY_PATH='/root/.opam/coqstoq/lib/stublibs:/root/.opam/coqstoq/lib/ocaml/stublibs:/root/.opam/coqstoq/lib/ocaml'
ENV OCAML_TOPLEVEL_PATH='/root/.opam/coqstoq/lib/toplevel'
ENV MANPATH='/root/.opam/coqstoq/man'
ENV PATH="/root/.opam/coqstoq/bin:$PATH"

# Poetry reqirements
RUN apt-get install -y pipx
RUN pipx install poetry
RUN pipx ensurepath
ENV PATH="/root/.local/bin:$PATH"

COPY ./test-repos /app/CoqStoq/test-repos
COPY ./test-theorems /app/CoqStoq/test-theorems
COPY ./test-theorems.json /app/CoqStoq/test-theorems.json

COPY ./val-repos /app/CoqStoq/val-repos
COPY ./val-theorems /app/CoqStoq/val-theorems
COPY ./val-theorems.json /app/CoqStoq/val-theorems.json

COPY ./cutoff-repos /app/CoqStoq/cutoff-repos
COPY ./cutoff-theorems /app/CoqStoq/cutoff-theorems
COPY ./cutoff-theorems.json /app/CoqStoq/cutoff-theorems.json

COPY ./README.md /app/CoqStoq/README.md
COPY ./pyproject.toml /app/CoqStoq/pyproject.toml
COPY ./poetry.lock /app/CoqStoq/poetry.lock
COPY ./coqpyt /app/CoqStoq/coqpyt
COPY ./coqstoq /app/CoqStoq/coqstoq

# Create virtual env 
WORKDIR /app/CoqStoq
RUN poetry env use /usr/bin/python3.12
RUN poetry install

# Build projects in the testing / validation / cutoff splits 
RUN poetry run python3 coqstoq/build_projects.py 



