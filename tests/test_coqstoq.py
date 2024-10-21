from coqstoq import Split, num_theorems, get_theorem, get_theorem_list
import logging


def test_coqstoq():
    for split in Split:
        assert num_theorems(split) == len(get_theorem_list(split))
        assert 0 < num_theorems(split)
        assert get_theorem(split, 0) == get_theorem_list(split)[0]
        assert (
            get_theorem(split, num_theorems(split) - 1) == get_theorem_list(split)[-1]
        )
