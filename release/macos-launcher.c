#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void resource_env(const char *key, const char *root, const char *suffix) {
    char value[PATH_MAX];
    snprintf(value, sizeof(value), "%s/%s", root, suffix);
    setenv(key, value, 1);
}

int main(int argc, char **argv) {
    (void)argc;
    char path[PATH_MAX], resolved[PATH_MAX], resources[PATH_MAX];
    uint32_t size = sizeof(path);
    if (_NSGetExecutablePath(path, &size) || !realpath(path, resolved)) return 1;
    char *end = strrchr(resolved, '/');
    if (!end) return 1;
    *end = 0;
    snprintf(path, sizeof(path), "%s/../Resources", resolved);
    if (!realpath(path, resources)) return 1;
    unsetenv("DYLD_LIBRARY_PATH");
    unsetenv("DYLD_FALLBACK_LIBRARY_PATH");
    resource_env("DYLD_FALLBACK_LIBRARY_PATH", resources, "coot/lib");
    resource_env("PYTHONHOME", resources, "coot");
    char python_path[PATH_MAX * 2];
    snprintf(python_path, sizeof(python_path),
             "%s/coot/lib/python3.14/site-packages:%s/coot/lib/python3.14/site-packages/coot",
             resources, resources);
    setenv("PYTHONPATH", python_path, 1);
    setenv("PYTHONNOUSERSITE", "1", 1);
    resource_env("GI_TYPELIB_PATH", resources, "coot/lib/girepository-1.0");
    resource_env("XDG_DATA_DIRS", resources, "coot/share");
    resource_env("GSETTINGS_SCHEMA_DIR", resources, "coot/share/glib-2.0/schemas");
    resource_env("COOT_PREFIX", resources, "coot");
    resource_env("COOT_DATA_DIR", resources, "coot/share/coot");
    resource_env("COOT_STANDARD_RESIDUES", resources, "coot/share/coot/standard-residues.pdb");
    resource_env("SYMINFO", resources, "coot/share/coot/data/syminfo.lib");
    if (!getenv("CLIBD_MON"))
        resource_env("CLIBD_MON", resources, "coot/share/coot/lib/data/monomers/");
    resource_env("COOT_REFMAC_LIB_DIR", resources, "coot/share/coot/lib");
    const char *user_home = getenv("HOME");
    if (user_home) {
        resource_env("XDG_CONFIG_HOME", user_home, "Library/Application Support/Coot-backbone-torsion/config");
        resource_env("XDG_CACHE_HOME", user_home, "Library/Caches/Coot-backbone-torsion");
        resource_env("XDG_STATE_HOME", user_home, "Library/Application Support/Coot-backbone-torsion/state");
    }
    setenv("LC_ALL", "C", 1);
    snprintf(path, sizeof(path), "%s/coot/libexec/MacCoot", resources);
    argv[0] = path;
    execv(path, argv);
    perror("Coot launch");
    return 1;
}
