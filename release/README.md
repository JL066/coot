# Coot 1.3.3 backbone torsion macOS prerelease

This is a targeted restoration based on upstream release commit
`0c588c81865cb6028c7ef33b161a35b33fd1b862`, not a build of current upstream main.
The application is `Coot-1.3.3-backbone-torsion-re.app` inside the ZIP.

## Changes

- Restore the visible Edit Backbone Torsions button, GTK4 atom picking,
  existing dialog, both rotation sliders, and Accept/Cancel cleanup.
- Restore the two live Ramachandran points using the existing
  `phi_psi_pairs_from_moving_atoms()` calculation and OpenGL HUD renderer.
  Classification and colors remain the existing Coot implementation.
  No GooCanvas, ordinary validation window, or new outlier counter is added.
- Protect the shared Python post-manipulation hook with the GIL to prevent
  the reproduced Accept crash.
- Package a relative-path launcher, Python/GTK and linked runtime libraries.
  Original installed applications are not changed.

Comparison: JL066/coot main was `186af296d7ec73fc1afe8320d8d181430d17bc5e`;
`fix/gtk4-backbone-torsion-editor` was
`589b59a2e444ec4515bc468d0eeb18f21900cc68`. That branch uses a later upstream
baseline and lacks this local Python-hook fix. This release therefore has a
dedicated branch rooted at 1.3.3, preserving the complete locally tested patch.
Core changes comprise 11 files, 108 insertions and 67 deletions; release
packaging and regression scripts are separate in this directory.

## Platform and limitations

Apple Silicon (arm64), macOS 26 or newer. The bundle is ad-hoc signed, not
Developer ID signed or notarized; macOS may require explicit user approval.
Keep your existing Coot installation. This is a prerelease pending physical
mouse interaction and broader regression testing, including Rotamer and Edit
Chi Angles. Automated GTK signals are not physical mouse acceptance tests.

The bundle includes Coot's standard monomer dictionary subset, not the complete
CCP4 distribution. External tools such as Refmac/Phenix and additional ligand
dictionaries are not bundled. An explicitly supplied CLIBD_MON is respected.
Third-party notices/formula metadata and dependency hashes are in Resources.

## Building and packaging

Build Coot out of tree using the project's Autotools build and its required
Homebrew dependencies. Configure a separate staging prefix inside a test app,
never an existing installation. The tested build used Python 3.14.7, GTK4,
Boost Python 3.14, Gemmi, RDKit, Clipper/FFTW2, GLM 1.0.3 and Apple Clang.
Configure options included `--with-boost`, `--with-boost-libdir`, `--with-gemmi`,
`--with-glm`, `--with-rdkit-prefix`, `--with-fftw-prefix`, `--with-backward`,
`--with-libdw`, `--with-netcdf`, `--with-sound`, `--with-vte`,
`BOOST_PYTHON_LIB=boost_python314` and `PYTHON=/opt/homebrew/bin/python3.14`.
Build with `make -j4` and install only into that staging prefix.

The release reuses the existing compiled and tested staging build after
checking its 11 modified tracked source files against this branch. The
pre-packaging libcootsumo.0.dylib SHA-256 was
`200c2bacb72df3e46b15d7b8ee0660a7f8ecd6ee29292a1a09b88eeba06c665d`.
Packaging changes Mach-O load commands and signatures, so its final hash differs.

On the matching build host:

```sh
python3 release/package-macos.py /path/to/staging.app /path/to/Coot-1.3.3-backbone-torsion-re.app
codesign --verify --deep --strict /path/to/Coot-1.3.3-backbone-torsion-re.app
```

The output must not already exist. The script copies the input, bundles the
dependency closure, rewrites load paths, signs the copy and rejects external
Homebrew/developer/application Mach-O dependencies. It assumes the recorded
Homebrew Python 3.14 package layout; it is not a generic installer.

## Regression checks

Copy the app to a different path containing spaces and use a clean HOME and
environment. Run `test-runtime.py` inside Coot via `--script` to verify module
locations. Build the test-only native probe with `rama-probe.mk` from the
original build's src directory, supplying absolute BUILD_DIR, RELEASE_DIR
and PROBE_OUTPUT. It is not part of the application.

Run `test-backbone-rama.py` with COOT_TEST_PROBE, COOT_TEST_SOURCE and
COOT_TEST_OUTPUT set. It exercises actual GTK scales, the GL renderer,
the two original phi/psi pairs, changing classifications, three editing cycles,
Accept coordinate submission, Cancel coordinate preservation and cleanup,
then the existing Real Space Refine HUD data source. The test captures GPU
framebuffers. `test-picking.py` exercises the visible button and actual GTK
click-controller signal through to the dialog and Cancel.

The full Coot test suite and physical mouse QA have not been run. Existing
macOS OpenGL texture warnings during refinement are still observed.
