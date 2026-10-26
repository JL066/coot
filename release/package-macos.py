"""Package an existing Coot installation; never modify the input bundle.

Usage: python3 package-macos.py INPUT.app OUTPUT.app
Requires the matching Homebrew runtime locally.
OUTPUT must not exist. Only OUTPUT is modified.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

def run(*args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f'{args}: {error.stderr}') from error

def macho(path):
    with path.open('rb') as f:
        return f.read(4) in (b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe')

def package(source, target):
    assert source.is_dir() and not target.exists()
    def ignore(directory, names):
        skipped = shutil.ignore_patterns('__pycache__', '*.pyc', '*.a', '*.la')(directory, names)
        if Path(directory) == source / 'Contents/MacOS':
            skipped.add('Coot')  # unused developer shell launcher
        return skipped
    shutil.copytree(source, target, symlinks=True, ignore=ignore)
    resources = target / 'Contents/Resources'
    prefix = resources / 'coot'
    old_prefix = source / 'Contents/Resources/coot'
    library = prefix / 'lib'
    origins = {}
    inventory = {}
    for p in target.rglob('*'):
        if p.is_file() and not p.is_symlink() and p.name != 'CootLauncher' and macho(p):
            origins[p] = source / p.relative_to(target)

    def copy_tree(src, dst):
        src = Path(src).resolve()
        shutil.copytree(src, dst, symlinks=False, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.a', '*.la', 'site-packages', 'sitecustomize.py'))
        for p in dst.rglob('*'):
            if 'site-packages' in p.relative_to(dst).parts:
                continue  # pre-existing Coot modules were not copied from stdlib
            if p.is_file() and macho(p):
                origins[p] = src / p.relative_to(dst)

    stdlib = Path('/opt/homebrew/opt/python@3.14/Frameworks/Python.framework/Versions/3.14/lib/python3.14')
    copy_tree(stdlib, prefix / 'lib/python3.14')
    python_exe = stdlib.parents[1] / 'bin/python3.14'
    shutil.copy2(python_exe.resolve(), prefix / 'bin/python3')
    origins[prefix / 'bin/python3'] = python_exe.resolve()
    site = prefix / 'lib/python3.14/site-packages'
    for name in ('gi', 'cairo', 'numpy', 'rdkit', 'PIL', 'gemmi'):
        copy_tree(Path('/opt/homebrew/lib/python3.14/site-packages') / name, site / name)
    copy_tree('/opt/homebrew/lib/girepository-1.0', library / 'girepository-1.0')
    for name in ('icons', 'glib-2.0'):
        copy_tree(Path('/opt/homebrew/share') / name, prefix / 'share' / name)

    def deps(p):
        ids = run('otool', '-D', str(p)).splitlines()[1:]
        return [line.strip().split(' (')[0] for line in run('otool', '-L', str(p)).splitlines()[1:]
                if line.strip().split(' (')[0] not in ids]

    def resolve(dep, origin):
        if dep.startswith('@loader_path/'):
            return (origin.parent / dep.removeprefix('@loader_path/')).resolve()
        if dep.startswith('@rpath/'):
            tail = dep.removeprefix('@rpath/')
            lines = run('otool', '-l', str(origin)).splitlines()
            candidates = []
            for i, line in enumerate(lines):
                if line.strip() == 'cmd LC_RPATH':
                    root = lines[i+2].strip().split(' (')[0].removeprefix('path ')
                    root = root.replace('@loader_path', str(origin.parent))
                    candidates.append(Path(root) / tail)
            candidates += [origin.parent / tail, Path('/opt/homebrew/lib') / tail]
            return next(p.resolve() for p in candidates if p.exists())
        return Path(dep).resolve()

    def include(dep, origin):
        if dep.startswith(('/usr/lib/', '/System/Library/')):
            return None
        if dep.startswith(str(old_prefix) + '/'):
            p = prefix / Path(dep).relative_to(old_prefix)
            assert p.exists(), p
            return p.resolve()
        src = resolve(dep, origin)
        if src == origin.resolve():
            return None  # the dylib's own install ID
        for bundled, original in origins.items():
            if original.resolve() == src:
                return bundled
        dst = library / src.name
        if dst.exists():
            if dst in origins:
                assert origins[dst].resolve() == src, (dst, src, origins[dst])
            return dst
        assert src.is_file(), src
        shutil.copy2(src, dst)
        origins[dst] = src
        inventory[str(src)] = hashlib.sha256(src.read_bytes()).hexdigest()
        return dst

    # Typelibs dlopen these libraries rather than linking them directly.
    for name in ('libgtk-4.1.dylib', 'libgirepository-1.0.1.dylib',
                 'libgdk_pixbuf-2.0.0.dylib', 'libgio-2.0.0.dylib'):
        include('/opt/homebrew/lib/' + name, old_prefix / 'libexec/MacCoot')
    done = set()
    while pending := [p for p in origins if p not in done]:
        for p in pending:
            changes = []
            for dep in deps(p):
                dest = include(dep, origins[p])
                if dest and dest != p:
                    changes += ['-change', dep, '@loader_path/' + os.path.relpath(dest, p.parent)]
            if p.suffix in ('.dylib', '.so') or p.name == 'Python':
                changes += ['-id', '@loader_path/' + p.name]
            if changes:
                run('install_name_tool', *changes, str(p))
            # Ad-hoc signatures are necessary after editing arm64 load commands.
            run('codesign', '--sign', '-', '--force', str(p))
            done.add(p)

    # A source URL/formula and license texts accompany each Homebrew dependency.
    notices = resources / 'ThirdPartyNotices'
    notices.mkdir()
    cells = set()
    for src in origins.values():
        parts = src.resolve().parts
        if 'Cellar' in parts:
            i = parts.index('Cellar')
            cells.add(Path(*parts[:i+3]))
    for cell in cells:
        dst = notices / cell.parent.name / cell.name
        dst.mkdir(parents=True)
        for p in cell.iterdir():
            if p.is_file() and (p.name.upper().startswith(('COPYING', 'LICENSE', 'NOTICE')) or p.name == 'INSTALL_RECEIPT.json'):
                shutil.copy2(p, dst / p.name)
        if (cell / '.brew').exists():
            shutil.copytree(cell / '.brew', dst / 'formula')
    shutil.copy2(Path(__file__).parents[1] / 'COPYING', resources / 'COPYING')
    (resources / 'dependency-manifest.json').write_text(json.dumps(inventory, indent=2) + '\n')
    launcher = target / 'Contents/MacOS/CootLauncher'
    run('clang', '-O2', '-Wall', '-Wextra', str(Path(__file__).with_name('macos-launcher.c')), '-o', str(launcher))
    info = target / 'Contents/Info.plist'
    data = plistlib.loads(info.read_bytes())
    data.update(CFBundleName='Coot-1.3.3-backbone-torsion-re',
                CFBundleDisplayName='Coot 1.3.3 Backbone Torsion',
                CFBundleIdentifier='org.coot.backbone-torsion-re', CFBundleVersion='1.3.3.1')
    info.write_bytes(plistlib.dumps(data))
    run('codesign', '--sign', '-', '--force', str(target))
    for p in done:
        external = [d for d in deps(p) if d.startswith(('/opt/', '/Users/', '/Applications/'))]
        assert not external, (p, external)
    print('Packaged and checked', len(done), 'Mach-O files:', target)

if __name__ == '__main__':
    package(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
