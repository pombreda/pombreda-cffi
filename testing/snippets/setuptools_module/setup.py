from setuptools import setup

from cffi.packaging import FFIExtension, build_ext

import ffibuilder


setup(
    data_files=['ffibuilder.py'],
    ext_modules=[FFIExtension(ffibuilder.build_ffi)],
    cmdclass={'build_ext': build_ext},
)
