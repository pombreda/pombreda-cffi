import cffi

ffi = cffi.FFI()

ffi.cdef("""
    extern "Python" {
        int add(int, int);
    }
""", dllexport=True)

ffi.embedding_init_code("""
    from _embedding_cffi import ffi
    print("preparing")   # printed once

    @ffi.def_extern()
    def add(x, y):
        print("adding %d and %d" % (x, y))
        return x + y
""")

ffi.set_source("_embedding_cffi", "")

ffi.compile(verbose=True)
