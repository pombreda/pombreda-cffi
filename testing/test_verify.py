import py
import math
from cffi import FFI, VerificationError, VerificationMissing


def test_missing_function():
    ffi = FFI()
    ffi.cdef("void some_completely_unknown_function();")
    py.test.raises(VerificationError, ffi.verify)

def test_simple_case():
    ffi = FFI()
    ffi.cdef("double sin(double x);")
    lib = ffi.verify('#include <math.h>')
    assert lib.sin(1.23) == math.sin(1.23)

def test_rounding_1():
    ffi = FFI()
    ffi.cdef("float sin(double x);")
    lib = ffi.verify('#include <math.h>')
    res = lib.sin(1.23)
    assert res != math.sin(1.23)     # not exact, because of double->float
    assert abs(res - math.sin(1.23)) < 1E-5

def test_rounding_2():
    ffi = FFI()
    ffi.cdef("double sin(float x);")
    lib = ffi.verify('#include <math.h>')
    res = lib.sin(1.23)
    assert res != math.sin(1.23)     # not exact, because of double->float
    assert abs(res - math.sin(1.23)) < 1E-5

def test_strlen_exact():
    ffi = FFI()
    ffi.cdef("size_t strlen(const char *s);")
    lib = ffi.verify("#include <string.h>")
    assert lib.strlen("hi there!") == 9

def test_strlen_approximate():
    ffi = FFI()
    ffi.cdef("int strlen(char *s);")
    lib = ffi.verify("#include <string.h>")
    assert lib.strlen("hi there!") == 9


all_integer_types = ['short', 'int', 'long', 'long long',
                     'signed char', 'unsigned char',
                     'unsigned short', 'unsigned int',
                     'unsigned long', 'unsigned long long']
all_float_types = ['float', 'double']

def test_all_integer_and_float_types():
    for typename in all_integer_types + all_float_types:
        ffi = FFI()
        ffi.cdef("%s foo(%s);" % (typename, typename))
        lib = ffi.verify("%s foo(%s x) { return x+1; }" % (typename, typename))
        assert lib.foo(42) == 43
        assert lib.foo(44L) == 45
        assert lib.foo(ffi.cast(typename, 46)) == 47
        py.test.raises(TypeError, lib.foo, None)
        #
        # check for overflow cases
        if typename in all_float_types:
            continue
        for value in [-2**80, -2**40, -2**20, -2**10, -2**5, -1,
                      2**5, 2**10, 2**20, 2**40, 2**80]:
            overflows = int(ffi.cast(typename, value)) != value
            if overflows:
                py.test.raises(OverflowError, lib.foo, value)
            else:
                assert lib.foo(value) == value + 1

def test_char_type():
    ffi = FFI()
    ffi.cdef("char foo(char);")
    lib = ffi.verify("char foo(char x) { return x+1; }")
    assert lib.foo("A") == "B"
    py.test.raises(TypeError, lib.foo, "bar")

def test_no_argument():
    ffi = FFI()
    ffi.cdef("int foo(void);")
    lib = ffi.verify("int foo() { return 42; }")
    assert lib.foo() == 42

def test_two_arguments():
    ffi = FFI()
    ffi.cdef("int foo(int, int);")
    lib = ffi.verify("int foo(int a, int b) { return a - b; }")
    assert lib.foo(40, -2) == 42

def test_macro():
    ffi = FFI()
    ffi.cdef("int foo(int, int);")
    lib = ffi.verify("#define foo(a, b) ((a) * (b))")
    assert lib.foo(-6, -7) == 42

def test_ptr():
    ffi = FFI()
    ffi.cdef("int *foo(int *);")
    lib = ffi.verify("int *foo(int *a) { return a; }")
    assert lib.foo(None) is None
    p = ffi.new("int", 42)
    q = ffi.new("int", 42)
    assert lib.foo(p) == p
    assert lib.foo(q) != p

def test_bogus_ptr():
    ffi = FFI()
    ffi.cdef("int *foo(int *);")
    lib = ffi.verify("int *foo(int *a) { return a; }")
    py.test.raises(TypeError, lib.foo, ffi.new("short", 42))


def test_verify_typedefs():
    py.test.skip("XXX?")
    types = ['signed char', 'unsigned char', 'int', 'long']
    for cdefed in types:
        for real in types:
            ffi = FFI()
            ffi.cdef("typedef %s foo_t;" % cdefed)
            if cdefed == real:
                ffi.verify("typedef %s foo_t;" % real)
            else:
                py.test.raises(VerificationError, ffi.verify,
                               "typedef %s foo_t;" % real)


def test_ffi_full_struct():
    py.test.skip("XXX?")
    ffi = FFI()
    ffi.cdef("struct foo_s { char x; int y; long *z; };")
    ffi.verify("struct foo_s { char x; int y; long *z; };")
    #
    for real in [
        "struct foo_s { char x; int y; int *z; };",
        "struct foo_s { char x; long *z; int y; };",
        "struct foo_s { int y; long *z; };",
        "struct foo_s { char x; int y; long *z; char extra; };",
        ]:
        py.test.raises(VerificationError, ffi.verify, real)
    #
    # a corner case that we cannot really detect, but where it has no
    # bad consequences: the size is the same, but there is an extra field
    # that replaces what is just padding in our declaration above
    ffi.verify("struct foo_s { char x, extra; int y; long *z; };")


def test_ffi_nonfull_struct():
    py.test.skip("XXX")
    ffi = FFI()
    ffi.cdef("""
    struct foo_s {
       int x;
       ...;
    };
    """)
    py.test.raises(VerificationMissing, ffi.sizeof, 'struct foo_s')
    py.test.raises(VerificationMissing, ffi.offsetof, 'struct foo_s', 'x')
    py.test.raises(VerificationMissing, ffi.new, 'struct foo_s')
    ffi.verify("""
    struct foo_s {
       int a, b, x, c, d, e;
    };
    """)
    assert ffi.sizeof('struct foo_s') == 6 * ffi.sizeof(int)
    assert ffi.offsetof('struct foo_s', 'x') == 2 * ffi.sizeof(int)
