import py
import recompiler
from cffi1 import FFI


def check_type_table(input, expected_output):
    ffi = FFI()
    ffi.cdef(input)
    recomp = recompiler.Recompiler(ffi, 'testmod')
    recomp.collect_type_table()
    assert ''.join(map(str, recomp.cffi_types)) == expected_output

def verify(*args, **kwds):
    kwds.setdefault('undef_macros', ['NDEBUG'])
    return recompiler.verify(*args, **kwds)


def test_type_table_func():
    check_type_table("double sin(double);",
                     "(FUNCTION 1)(PRIMITIVE 14)(FUNCTION_END 0)")
    check_type_table("float sin(double);",
                     "(FUNCTION 3)(PRIMITIVE 14)(FUNCTION_END 0)(PRIMITIVE 13)")
    check_type_table("float sin(void);",
                     "(FUNCTION 2)(FUNCTION_END 0)(PRIMITIVE 13)")
    check_type_table("double sin(float); double cos(float);",
                     "(FUNCTION 3)(PRIMITIVE 13)(FUNCTION_END 0)(PRIMITIVE 14)")
    check_type_table("double sin(float); double cos(double);",
                     "(FUNCTION 1)(PRIMITIVE 14)(FUNCTION_END 0)"   # cos
                     "(FUNCTION 1)(PRIMITIVE 13)(FUNCTION_END 0)")  # sin
    check_type_table("float sin(double); float cos(float);",
                     "(FUNCTION 4)(PRIMITIVE 14)(FUNCTION_END 0)"   # sin
                     "(FUNCTION 4)(PRIMITIVE 13)(FUNCTION_END 0)")  # cos

def test_use_noop_for_repeated_args():
    check_type_table("double sin(double *, double *);",
                     "(FUNCTION 4)(POINTER 4)(NOOP 1)(FUNCTION_END 0)"
                     "(PRIMITIVE 14)")
    check_type_table("double sin(double *, double *, double);",
                     "(FUNCTION 3)(POINTER 3)(NOOP 1)(PRIMITIVE 14)"
                     "(FUNCTION_END 0)")

def test_dont_use_noop_for_primitives():
    check_type_table("double sin(double, double);",
                     "(FUNCTION 1)(PRIMITIVE 14)(PRIMITIVE 14)(FUNCTION_END 0)")

def test_funcptr_as_argument():
    check_type_table("int sin(double(float));",
                     "(FUNCTION 6)(PRIMITIVE 13)(FUNCTION_END 0)"
                     "(FUNCTION 7)(POINTER 0)(FUNCTION_END 0)"
                     "(PRIMITIVE 14)(PRIMITIVE 7)")

def test_variadic_function():
    check_type_table("int sin(int, ...);",
                     "(FUNCTION 1)(PRIMITIVE 7)(FUNCTION_END 1)")

def test_array():
    check_type_table("int a[100];",
                     "(PRIMITIVE 7)(ARRAY 0)(None 100)")

def test_typedef():
    check_type_table("typedef int foo_t;",
                     "(PRIMITIVE 7)")

def test_prebuilt_type():
    check_type_table("int32_t f(void);",
                     "(FUNCTION 2)(FUNCTION_END 0)(PRIMITIVE 21)")

def test_struct_opaque():
    check_type_table("struct foo_s;",
                     "(STRUCT_UNION 0)")

def test_struct():
    check_type_table("struct foo_s { int a; long b; };",
                     "(PRIMITIVE 7)(PRIMITIVE 9)(STRUCT_UNION 0)")

def test_union():
    check_type_table("union foo_u { int a; long b; };",
                     "(PRIMITIVE 7)(PRIMITIVE 9)(STRUCT_UNION 0)")

def test_struct_used():
    check_type_table("struct foo_s { int a; long b; }; int f(struct foo_s*);",
                     "(FUNCTION 3)(POINTER 5)(FUNCTION_END 0)"
                     "(PRIMITIVE 7)(PRIMITIVE 9)"
                     "(STRUCT_UNION 0)")


def test_math_sin():
    import math
    ffi = FFI()
    ffi.cdef("float sin(double); double cos(double);")
    lib = verify(ffi, 'test_math_sin', '#include <math.h>')
    assert lib.cos(1.43) == math.cos(1.43)

def test_funcarg_ptr():
    ffi = FFI()
    ffi.cdef("int foo(int *);")
    lib = verify(ffi, 'test_funcarg_ptr', 'int foo(int *p) { return *p; }')
    assert lib.foo([-12345]) == -12345

def test_funcres_ptr():
    ffi = FFI()
    ffi.cdef("int *foo(void);")
    lib = verify(ffi, 'test_funcres_ptr',
                 'int *foo(void) { static int x=-12345; return &x; }')
    assert lib.foo()[0] == -12345

def test_global_var_array():
    ffi = FFI()
    ffi.cdef("int a[100];")
    lib = verify(ffi, 'test_global_var_array', 'int a[100] = { 9999 };')
    lib.a[42] = 123456
    assert lib.a[42] == 123456
    assert lib.a[0] == 9999

def test_verify_typedef():
    ffi = FFI()
    ffi.cdef("typedef int **foo_t;")
    lib = verify(ffi, 'test_verify_typedef', 'typedef int **foo_t;')
    assert ffi.sizeof("foo_t") == ffi.sizeof("void *")

def test_global_var_int():
    ffi = FFI()
    ffi.cdef("int a, b, c;")
    lib = verify(ffi, 'test_global_var_int', 'int a = 999, b, c;')
    assert lib.a == 999
    lib.a -= 1001
    assert lib.a == -2
    lib.a = -2147483648
    assert lib.a == -2147483648
    py.test.raises(OverflowError, "lib.a = 2147483648")
    py.test.raises(OverflowError, "lib.a = -2147483649")
    lib.b = 525      # try with the first access being in setattr, too
    assert lib.b == 525
    py.test.raises(AttributeError, "del lib.a")
    py.test.raises(AttributeError, "del lib.c")
    py.test.raises(AttributeError, "del lib.foobarbaz")

def test_macro():
    ffi = FFI()
    ffi.cdef("#define FOOBAR ...")
    lib = verify(ffi, 'test_macro', "#define FOOBAR (-6912)")
    assert lib.FOOBAR == -6912
    py.test.raises(AttributeError, "lib.FOOBAR = 2")

def test_constant():
    ffi = FFI()
    ffi.cdef("static const int FOOBAR;")
    lib = verify(ffi, 'test_constant', "#define FOOBAR (-6912)")
    assert lib.FOOBAR == -6912
    py.test.raises(AttributeError, "lib.FOOBAR = 2")

def test_constant_nonint():
    ffi = FFI()
    ffi.cdef("static const double FOOBAR;")
    lib = verify(ffi, 'test_constant_nonint', "#define FOOBAR (-6912.5)")
    assert lib.FOOBAR == -6912.5
    py.test.raises(AttributeError, "lib.FOOBAR = 2")

def test_constant_ptr():
    ffi = FFI()
    ffi.cdef("static double *const FOOBAR;")
    lib = verify(ffi, 'test_constant_ptr', "#define FOOBAR NULL")
    py.test.skip("XXX in-progress:")
    assert lib.FOOBAR == ffi.NULL
    assert ffi.typeof(lib.FOOBAR) == ffi.typeof("double *")

def test_dir():
    ffi = FFI()
    ffi.cdef("int ff(int); int aa; static const int my_constant;")
    lib = verify(ffi, 'test_dir', """
        #define my_constant  (-45)
        int aa;
        int ff(int x) { return x+aa; }
    """)
    lib.aa = 5
    assert dir(lib) == ['aa', 'ff', 'my_constant']

def test_verify_opaque_struct():
    ffi = FFI()
    ffi.cdef("struct foo_s;")
    lib = verify(ffi, 'test_verify_opaque_struct', "struct foo_s;")
    assert ffi.typeof("struct foo_s").cname == "struct foo_s"

def test_verify_opaque_union():
    ffi = FFI()
    ffi.cdef("union foo_s;")
    lib = verify(ffi, 'test_verify_opaque_union', "union foo_s;")
    assert ffi.typeof("union foo_s").cname == "union foo_s"

def test_verify_struct():
    ffi = FFI()
    ffi.cdef("""struct foo_s { int b; short a; };
                struct bar_s { struct foo_s *f; };""")
    lib = verify(ffi, 'test_verify_struct',
                 """struct foo_s { short a; int b; };
                    struct bar_s { struct foo_s *f; };""")
    ffi.typeof("struct bar_s *")
    p = ffi.new("struct foo_s *", {'a': -32768, 'b': -2147483648})
    assert p.a == -32768
    assert p.b == -2147483648
    py.test.raises(OverflowError, "p.a -= 1")
    py.test.raises(OverflowError, "p.b -= 1")
    q = ffi.new("struct bar_s *", {'f': p})
    assert q.f == p

def test_type_caching():
    ffi1 = FFI(); ffi1.cdef("struct foo_s;")
    ffi2 = FFI(); ffi2.cdef("struct foo_s;")    # different one!
    lib1 = verify(ffi1, 'test_type_caching_1', 'struct foo_s;')
    lib2 = verify(ffi2, 'test_type_caching_2', 'struct foo_s;')
    # shared types
    assert ffi1.typeof("long") is ffi2.typeof("long")
    assert ffi1.typeof("long**") is ffi2.typeof("long * *")
    assert ffi1.typeof("long(*)(int, ...)") is ffi2.typeof("long(*)(int, ...)")
    # non-shared types
    assert ffi1.typeof("struct foo_s") is not ffi2.typeof("struct foo_s")
    assert ffi1.typeof("struct foo_s *") is not ffi2.typeof("struct foo_s *")
    assert ffi1.typeof("struct foo_s*(*)()") is not (
        ffi2.typeof("struct foo_s*(*)()"))
    assert ffi1.typeof("void(*)(struct foo_s*)") is not (
        ffi2.typeof("void(*)(struct foo_s*)"))

def test_dotdotdot_length_of_array_field():
    ffi = FFI()
    ffi.cdef("struct foo_s { int a[...]; int b[...]; };")
    verify(ffi, 'test_dotdotdot_length_of_array_field',
           "struct foo_s { int a[42]; int b[11]; };")
    assert ffi.sizeof("struct foo_s") == (42 + 11) * 4
    p = ffi.new("struct foo_s *")
    assert p.a[41] == p.b[10] == 0
    py.test.raises(IndexError, "p.a[42]")
    py.test.raises(IndexError, "p.b[11]")

def test_dotdotdot_global_array():
    ffi = FFI()
    ffi.cdef("int aa[...]; int bb[...];")
    lib = verify(ffi, 'test_dotdotdot_global_array',
                 "int aa[41]; int bb[12];")
    assert ffi.sizeof(lib.aa) == 41 * 4
    assert ffi.sizeof(lib.bb) == 12 * 4
    assert lib.aa[40] == lib.bb[11] == 0
    py.test.raises(IndexError, "lib.aa[41]")
    py.test.raises(IndexError, "lib.bb[12]")

