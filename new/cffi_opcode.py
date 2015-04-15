
class CffiOp(object):
    def __init__(self, op, arg):
        self.op = op
        self.arg = arg
    def as_int(self):
        return self.op | (self.arg << 8)
    def __str__(self):
        classname = CLASS_NAME.get(self.op, self.op)
        return '(%s %d)' % (classname, self.arg)

OP_PRIMITIVE       = 1
OP_POINTER         = 3
OP_ARRAY           = 5
OP_OPEN_ARRAY      = 7
OP_STRUCT_UNION    = 9
OP_ENUM            = 11
OP_TYPENAME        = 13
OP_FUNCTION        = 15
OP_FUNCTION_END    = 17
OP_NOOP            = 19
OP_BITFIELD        = 21
OP_CPYTHON_BLTN_V  = 23   # varargs
OP_CPYTHON_BLTN_N  = 25   # noargs
OP_CPYTHON_BLTN_O  = 27   # O  (i.e. a single arg)

PRIM_VOID          = 0
PRIM_BOOL          = 1
PRIM_CHAR          = 2
PRIM_SCHAR         = 3
PRIM_UCHAR         = 4
PRIM_SHORT         = 5
PRIM_USHORT        = 6
PRIM_INT           = 7
PRIM_UINT          = 8
PRIM_LONG          = 9
PRIM_ULONG         = 10
PRIM_LONGLONG      = 11
PRIM_ULONGLONG     = 12
PRIM_FLOAT         = 13
PRIM_DOUBLE        = 14
PRIM_LONGDOUBLE    = 15

PRIMITIVE_TO_INDEX = {
    'int':    PRIM_INT,
    'float':  PRIM_FLOAT,
    'double': PRIM_DOUBLE,
    }

CLASS_NAME = {}
for _name, _value in globals().items():
    if _name.startswith('OP_') and isinstance(_value, int):
        CLASS_NAME[_value] = _name[3:]
