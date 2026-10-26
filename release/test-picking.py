"""Regression: toolbar signal -> GtkGestureClick -> torsion dialog.

Run with the isolated CootLauncher --script option. Uses a synthetic GTK
signal, not an assertion that physical mouse interaction has been tested.
"""
import os
import coot
from gi.repository import GLib, Gtk

imol = coot.read_pdb(os.path.join(os.environ['COOT_TEST_SOURCE'], 'data/pdb-templates/theor-helix-70.pdb'))
target = next(a for a in coot.residue_info_py(imol, 'A', 35, '') if a[0][0] == ' CA ')
coot.set_rotation_centre(*target[2])

def descendants(w):
    c = w.get_first_child()
    while c:
        yield c
        yield from descendants(c)
        c = c.get_next_sibling()

def run():
    widgets = [w for top in Gtk.Window.list_toplevels() for w in descendants(top)]
    button = next(w for w in widgets if isinstance(w, Gtk.Button) and
                  any(isinstance(c, Gtk.Label) and c.get_label() == 'Edit Backbone Torsions'
                      for c in descendants(w)))
    area = next(w for w in widgets if isinstance(w, Gtk.GLArea))
    before = coot.molecule_to_pdb_string_py(imol)
    button.emit('clicked')
    controllers = area.observe_controllers()
    click = next(controllers.get_item(i) for i in range(controllers.get_n_items())
                 if isinstance(controllers.get_item(i), Gtk.GestureClick))
    click.emit('pressed', 1, area.get_width()/2, area.get_height()/2)
    dialog = next(w for w in Gtk.Window.list_toplevels()
                  if w.get_title() == 'Edit Backbone Torsions')
    assert dialog.get_visible(), 'toolbar -> click does not show torsion dialog'
    next(w for w in descendants(dialog) if isinstance(w, Gtk.Button)
         and (w.get_label() or '').strip() == 'Cancel').emit('clicked')
    assert not dialog.get_visible()
    assert coot.molecule_to_pdb_string_py(imol) == before
    print('PASS toolbar -> GTK click -> visible torsion dialog -> Cancel', flush=True)
    return False

GLib.timeout_add(3000, run)
