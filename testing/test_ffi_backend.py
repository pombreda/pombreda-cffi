import py
from testing import backend_tests, test_function, test_ownlib
from cffi import FFI
import _cffi_backend


class TestFFI(backend_tests.BackendTests,
              test_function.TestFunction,
              test_ownlib.TestOwnLib):
    TypeRepr = "<ctype '%s'>"

    @staticmethod
    def Backend():
        return _cffi_backend

    def test_not_supported_bitfield_in_result(self):
        ffi = FFI(backend=self.Backend())
        ffi.cdef("struct foo_s { int a,b,c,d,e; int x:1; };")
        e = py.test.raises(NotImplementedError, ffi.callback,
                           "struct foo_s foo(void)", lambda: 42)
        assert str(e.value) == ("<struct foo_s(*)(void)>: "
            "cannot pass as argument or return value a struct with bit fields")

    def test_inspecttype(self):
        ffi = FFI(backend=self.Backend())
        assert ffi.inspecttype("long") == ("primitive", "long")
        assert ffi.inspecttype(ffi.typeof("long")) == ("primitive", "long")
        pointer, LongP = ffi.inspecttype("long**")
        assert pointer == "pointer"
        pointer, Long = ffi.inspecttype(LongP)
        assert pointer == "pointer"
        assert ffi.inspecttype(Long) == ("primitive", "long")
        assert ffi.inspecttype("long(*)(long, long, ...)")[:4] == (
            "function", (Long, Long), Long, True)
