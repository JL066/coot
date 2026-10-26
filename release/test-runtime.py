"""Run inside the relocated app with --script, under a clean environment."""
import os
import sys
import coot
import coot_utils
import gi
import numpy
import rdkit
from gi.repository import Gtk

prefix = os.path.realpath(os.environ['COOT_PREFIX'])
assert os.path.realpath(sys.prefix) == prefix, (sys.prefix, prefix)
for module in (coot, coot_utils, gi, numpy, rdkit):
    location = os.path.realpath(module.__file__)
    assert location.startswith(prefix + '/'), (module.__name__, location)
assert all(not p.startswith(('/opt/homebrew', '/Applications/')) for p in sys.path), sys.path
assert Gtk.get_major_version() == 4
print('PASS packaged Python, GTK, NumPy, RDKit and Coot module locations', flush=True)
