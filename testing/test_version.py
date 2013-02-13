import py, os
import cffi, _cffi_backend

BACKEND_VERSIONS = {
    '0.4.2': '0.4',     # did not change
    }

def test_version():
    v = cffi.__version__
    version_info = '.'.join(str(i) for i in cffi.__version_info__)
    assert v == version_info
    assert BACKEND_VERSIONS.get(v, v) == _cffi_backend.__version__

def test_doc_version():
    parent = os.path.dirname(os.path.dirname(__file__))
    p = os.path.join(parent, 'doc', 'source', 'conf.py')
    content = open(p).read()
    #
    v = cffi.__version__
    assert ("version = '%s'\n" % v) in content
    assert ("release = '%s'\n" % v) in content

def test_doc_version_file():
    parent = os.path.dirname(os.path.dirname(__file__))
    v = cffi.__version__
    p = os.path.join(parent, 'doc', 'source', 'index.rst')
    content = open(p).read()
    if ("cffi/cffi-%s.tar.gz" % v) not in content:
        py.test.skip("XXX fix the file referenced by the doc!")

def test_setup_version():
    parent = os.path.dirname(os.path.dirname(__file__))
    p = os.path.join(parent, 'setup.py')
    content = open(p).read()
    #
    v = cffi.__version__
    assert ("version='%s'" % v) in content

def test_c_version():
    parent = os.path.dirname(os.path.dirname(__file__))
    v = cffi.__version__
    p = os.path.join(parent, 'c', 'test_c.py')
    content = open(p).read()
    assert ('assert __version__ == "%s"' % v) in content
