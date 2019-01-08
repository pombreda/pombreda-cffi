# pkg-config, https://www.freedesktop.org/wiki/Software/pkg-config/ integration for cffi
import subprocess

def is_installed():
    """Check if pkg-config is installed or not"""
    try:
        subprocess.check_output(["pkg-config", "--version"])
        return True
    except subprocess.CalledProcessError:
        return False


def merge_flags(cfg1, cfg2):
    """Merge values from cffi config flags cfg2 to cf1

    Example:
        merge_flags({"libraries": ["one"]}, {"libraries": "two"})
        {"libraries}" : ["one", "two"]}
    """
    for key, value in cfg2.items():
        if not key in cfg1:
            cfg1 [key] = value
        else:
            cfg1 [key].extend(value)
    return cfg1


def call(libname, flag):
    """Calls pkg-config and returing the output"""
    a = ["pkg-config", "--print-errors"]
    a.append(flag)
    a.append(libname)
    return subprocess.check_output(a)


def flags(libs):
    r"""Return compiler line flags for FFI.set_source based on pkg-config output

    Usage
        ...
        ffibuilder.set_source("_foo", libraries = ["foo", "bar"], pkgconfig = ["libfoo", "libbar"])

    If `pkg-config` is installed on build machine, then arguments
    `include_dirs`, `library_dirs`, `libraries`, `define_macros`,
    `extra_compile_args` and `extra_link_args` are extended with an output of
    `pkg-config` for `libfoo` and `libbar`.
    """

    # make API great again!
    if isinstance(libs, (str, bytes)):
        libs = (libs, )
    
    # drop starting -I -L -l from cflags
    def dropILl(string):
        def _dropILl(string):
            if string.startswith(b"-I") or string.startswith(b"-L") or string.startswith(b"-l"):
                return string [2:]
        return [_dropILl(x) for x in string.split()]

    # convert -Dfoo=bar to list of tuples [("foo", "bar")] expected by cffi
    def macros(string):
        def _macros(string):
            return tuple(string [2:].split(b"=", 2))
        return [_macros(x) for x in string.split() if x.startswith(b"-D")]

    def drop_macros(string):
        return [x for x in string.split() if not x.startswith(b"-D")]

    # return kwargs for given libname
    def kwargs(libname):
        return {
                "include_dirs" : dropILl(call(libname, "--cflags-only-I")),
                "library_dirs" : dropILl(call(libname, "--libs-only-L")),
                "libraries" : dropILl(call(libname, "--libs-only-l")),
                "define_macros" : macros(call(libname, "--cflags-only-other")),
                "extra_compile_args" : drop_macros(call(libname, "--cflags-only-other")),
                "extra_link_args" : call(libname, "--libs-only-other").split()
                }

    # merge all arguments together
    ret = {}
    for libname in libs:
        foo = kwargs(libname)
        merge_flags(ret, foo)

    return ret
