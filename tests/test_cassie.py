from .context import cassie
import numpy as np
from pytest import approx, raises

def test_basic():
    test = 1
    assert test == 1