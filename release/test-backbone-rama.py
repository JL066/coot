"""On-device GTK/GL regression; not a substitute for physical mouse QA.

Run with isolated CootLauncher --script. The native probe is test-only and
reads existing renderer state; it adds no Coot API or classification rules.
"""
import ctypes
import math
import os
import coot
from gi.repository import GLib, Gtk

probe = ctypes.CDLL(os.environ['COOT_TEST_PROBE'])
probe.rama_probe.argtypes = [ctypes.POINTER(ctypes.c_double)]
probe.rama_capture.argtypes = [ctypes.c_char_p]
root = os.environ['COOT_TEST_SOURCE'].rstrip('/') + '/'
output = os.environ['COOT_TEST_OUTPUT'].rstrip('/')
imol = coot.read_pdb(root + 'data/pdb-templates/theor-helix-70.pdb')
atom = next(a for a in coot.residue_info_py(imol, 'A', 35, '') if a[0][0] == ' CA ')
coot.set_rotation_centre(*atom[2])

def descendants(w):
    c = w.get_first_child()
    while c:
        yield c
        yield from descendants(c)
        c = c.get_next_sibling()

def state():
    # macOS may throttle background/occluded windows. Exercise the actual
    # GLArea renderer explicitly so checks do not depend on window focus.
    if 'test_area' in globals():
        test_area.make_current()
        test_area.attach_buffers()
        test_area.emit('render', test_area.get_context())
    data = (ctypes.c_double * 12)()
    probe.rama_probe(data)
    return list(data)

def controls():
    dialog = next(w for w in Gtk.Window.list_toplevels()
                  if w.get_title() == 'Edit Backbone Torsions')
    widgets = list(descendants(dialog))
    return ([w for w in widgets if isinstance(w, Gtk.Scale)],
            {w.get_label().strip(): w for w in widgets
             if isinstance(w, Gtk.Button) and w.get_label()})

def scenario():
    global test_area
    area = next(w for top in Gtk.Window.list_toplevels() for w in descendants(top)
                if isinstance(w, Gtk.GLArea))
    test_area = area
    captured = set()
    for cycle in range(3):
        before = coot.molecule_to_pdb_string_py(imol)
        coot.execute_setup_backbone_torsion_edit(imol, atom[3])
        yield
        initial = state()
        assert initial[0] == 1 and initial[1] == 2, initial
        scales, buttons = controls()
        classifications = set()
        for scale in scales:
            positions = set()
            for angle in range(-120, 121, 15):
                scale.set_value(angle)
                yield
                current = state()
                if current[2] not in captured:
                    name = (output + '/rama-feedback-outliers-%d.png' % current[2])
                    assert probe.rama_capture(name.encode()), name
                    captured.add(current[2])
                assert current[0] == 1 and current[1] == 2, current
                expected = [math.degrees(x) for x in current[4:8]]
                assert all(abs(x-y) < 0.001 for x, y in zip(expected, current[8:12])), current
                positions.add(tuple(round(x, 3) for x in current[8:12]))
                classifications.add(current[2])
            assert len(positions) > 10, positions
            scale.set_value(0)
            yield
        assert len(classifications) > 1, classifications
        scales[0].set_value(30)
        yield
        action = 'Accept' if cycle == 1 else 'Cancel'
        buttons[action].emit('clicked')
        yield
        assert state()[0] == 0, state()
        assert probe.rama_capture((output + '/rama-after-%s-%d.png'
                                   % (action.lower(), cycle)).encode())
        after = coot.molecule_to_pdb_string_py(imol)
        assert (after != before) if action == 'Accept' else (after == before)
        print('PASS Rama cycle', cycle, action, 'two points track original angles; classifications',
              sorted(classifications), flush=True)
    # Exercise Real Space Refine with the repository's matching tutorial data.
    model = coot.read_pdb(root + 'data/tutorial-modern.pdb')
    density = coot.make_and_draw_map(root + 'data/rnasa-1.8-all_refmac1.mtz',
                                    'FWT', 'PHWT', '', 0, 0)
    assert density >= 0
    coot.set_imol_refinement_map(density)
    before_refinement = coot.molecule_to_pdb_string_py(model)
    coot.refine_zone(model, 'A', 32, 38, '')
    for _ in range(15):
        yield
    normal = state()
    assert normal[0] == 0 and normal[3] == 1 and normal[1] > 2, normal
    assert probe.rama_capture((output + '/rama-real-space-refine.png').encode())
    coot.clear_up_moving_atoms()
    yield
    assert state()[0] == 0 and state()[3] == 0
    assert coot.molecule_to_pdb_string_py(model) == before_refinement
    print('PASS existing Real Space Refine HUD data source restored', flush=True)
    print('PASS RAMA ADAPTER CHECKS', flush=True)

steps = scenario()
def tick():
    try:
        next(steps)
        return True
    except StopIteration:
        return False

GLib.timeout_add(3000, lambda: (GLib.timeout_add(200, tick), False)[1])
