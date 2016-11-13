import collections as _collections

from itertools import chain
from importlib import reload

print_ = print

class _Flag():
    pass
_flag = _Flag()

#TODO change self.__class__ to type(self) and other magic accesses
# like self.__magicattr__ to super(object, self).__magicattr__ so that
# if self overrides __getattribute__ these are not broken.
# Hell maybe even do super(type, type(self)).__magicmethod__(self) to
# defend against custom behaviour defined in type(self)

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

def make_decorator(function):
    def decorator(fn):
        ret = function(fn)
        ret.__name__ = fn.__name__
        if hasattr(ret, '__dict__'):
            ret.__dict__.update(fn.__dict__)
        return ret
    return decorator

@make_decorator
def closure(f):
    return f()

def itemsetter(*items):
    if len(items) == 1:
        item = items[0]
        def g(obj, value):
            obj[item] = value
    else:
        def g(obj, values):
            for item, value in zip(items, values):
                obj[item] = value
    return g


class Break(BaseException):
    pass

########################################################################
#                         ATTRIBUTE ACCESSING                          #
########################################################################

class Attribute(str):
    _aa_insts = {}
    def __new__(cls, name):
        try:
            return cls._aa_insts[cls, name]
        except KeyError:
            inst = super().__new__(cls, name)
            cls._aa_insts[cls, name] = inst
            return inst

    def __repr__(self):
        return "<.{}>".format(self)

    def __call__(self, obj=None, set=_flag, dlt=_flag):
        if dlt is not _flag:
            return delattr(obj, self)
        if set is not _flag:
            return setattr(obj, self, set)
        else:
            return getattr(obj, self)

class _AttributeAccess():
    def __getattr__(self, attr):
        return Attribute(attr)

    def __call__(self, *args):
        def gen_aa_fn(obj):
            for a in args:
                yield a(obj)
        return gen_aa_fn

    def __getitem__(self, args):
        def list_aa_fn(obj):
            return [a(obj) for a in args]
        return list_aa_fn


attribute_accessor = _AttributeAccess()

########################################################################
#               CUSTOM           DICT            OBJECT                #
########################################################################

def _mydict_init_items_(*args, **kwargs):
    items = ()
    if len(args) == 3:
        space = args[2]
        for k in list(space.keys()):
            if str.startswith(k, '__') and str.endswith(k, '__'):
                del space[k]
        items = space.items()
    elif args and isinstance(args[0], _collections.Mapping):
        items = args[0].items()
    elif args and isinstance(args[0], _collections.Iterable):
        items = args[0]
    if kwargs:
        items = chain(items, kwargs.items())
    return items

def _mydict_pretty_factory_(start='{', end='}', relater=': ', delimiter=',',
                            key_action=lambda p, k: p.pretty(k), base=None):
    def _repr_pretty_(obj, p, cycle):
        nonlocal start, end, relater, delimiter, key_action, base
        typ = type(obj)

        beginning = typ.__name__ + '(' + start
        ending = end + ")"

        if typ is not base and typ.__repr__ != base.__repr__:
            # If the subclass provides its own repr, use it instead.
            return p.text(typ.__repr__(obj))

        if cycle:
            return p.text(beginning + '...' + ending)
        p.begin_group(1, beginning)
        keys = typ.keys(obj)
        # if dict isn't large enough to be truncated,
        #   sort keys before displaying
        if not (p.max_seq_length and len(obj) >= p.max_seq_length):
            try:
                keys = sorted(keys)
            except Exception:
                # Sometimes the keys don't sort.
                pass
        for idx, key in p._enumerate(keys):
            if idx:
                p.text(delimiter)
                p.breakable()
            key_action(p, key)
            p.text(relater)
            p.pretty(obj[key])
        p.end_group(1, ending)
    return _repr_pretty_

def add_mydict_pprinter(*args, **kwargs):
    def decorator(cls):
        kwds = dict(kwargs)
        kwds['base'] = cls
        cls._repr_pretty_ = _mydict_pretty_factory_(*args, **kwds)
        return cls
    return decorator


class DefaultSlots(type):
    def __new__(meta, name, bases, attrs):
        if '__slots__' not in attrs:
            attrs['__slots__'] = ()
        return super().__new__(meta, name, bases, attrs)

@add_mydict_pprinter()
class DictObject(dict, metaclass=DefaultSlots):
    def __init__(self, *args, **kwargs):
        data = ((k if not isinstance(k, str) else Attribute(k), v)
                for k, v in _mydict_init_items_(*args, **kwargs))
        super().__init__(data)
    
    def __repr__(self):
        return "{}({})".format(type(self).__name__, super().__repr__())

    
    def __getattribute__(self, name):
        try:
            return self[name]
        except KeyError:
            errstr = "'{}' object has no attribute '{}'"
            raise AttributeError(errstr.format(type(self).__name__, name))

    def __setattr__(self, name, value):
        self[Attribute(name)] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)

@add_mydict_pprinter('', '', '=', ',', lambda p, k: p.text(k))
class Namespace(DictObject):
    def __init__(self, *args, **kwargs):
        items = _mydict_init_items_(*args, **kwargs)
        data = ((Attribute(k), v) for k, v in items if
                isinstance(k, str) and str.isidentifier(k))
        super(__class__, type(self)).__init__(self, data)

    def __setattr__(self, name, value):
        if not isinstance(name, str) or not str.isidentifier(name):
            errstr = "{} is not a valid attribute name identifier"
            raise ValueError(errstr.format(name))
        self[Attribute(name)] = value

    def __repr__(self):
        attach = __class__.__repr__
        is_orig = False
        if not hasattr(attach, '_seen'):
            is_orig = True
            attach._seen = {}
        elif id(self) in attach._seen:
            return type(self).__name__ + "(...)"
        attach._seen[id(self)] = self
        try:
            it = type(self).items(self)
            body = ', '.join("{}={}".format(a, repr(v)) for a, v in it)
            return "{}({})".format(type(self).__name__, body)
        finally:
            del attach._seen[id(self)]
            if is_orig:
                del attach._seen

    def mycopy(self, copied={}):
        is_orig = not copied
        selfc = copied[id(self)] = type(self)()
        for key, obj in type(self).items(self):
            if isinstance(obj, __class__):
                if id(obj) in copied:
                    selfc[key] = copied[id(obj)]
                else:
                    selfc[key] = type(obj).mycopy(obj, copied=copied)
            else:
                selfc[key] = obj
        if is_orig:
            copied.clear()
        return selfc

def copy(obj):
    assert(isinstance(obj, Namespace))
    return type(obj).mycopy(obj)

def revise(obj: Namespace, src: dict, revised=set()):
    is_orig = not revised
    revised.add(id(obj))
    for key, item in type(obj).items(obj):
        if isinstance(item, Namespace):
            if id(item) not in revised:
                revise(item, src[key], revised=revised)
        else:
            obj[key] = src[key]
    if is_orig:
        revised.clear()

########################################################################

def multiline_code(codestr):
    rc = _re.compile(r'\n\s*')
    indent = rc.match(codestr).group()
    return codestr.replace(indent, '\n')

    
def compose(*args, r2l=False):
    funclist = list(args)
    if r2l:
        funclist.reverse()
    def composed_function(*args, **kwargs):
        res = funclist[0](*args, **kwargs)
        for f in funclist[1:]:
            res = f(res)
        return res
    return composed_function

def merged_dict(*dicts):
    if len(dicts) == 1 and isinstance(dicts[0], _types.GeneratorType):
        dicts = dicts[0]
    ret = {}
    for d in dicts:
        ret.update(d)
    return ret

# math/functional
def identity(x):
    return x

def prod(iterable, start=1):
    product = start
    for x in iterable:
        product *= x
    return product

def adder(left=None, right=None):
    if left is not None:
        return lambda x: left + x
    elif right is not None:
        return lambda x: x + right
    else:
        raise TypeError("operation only takes one of left or right")

def scaler(left=None, right=None):
    if left is not None:
        return lambda x: left * x
    elif right is not None:
        return lambda x: x * right
    else:
        raise TypeError("operation only takes one of left or right")

def power(exponent):
    return lambda x: x ** exponent

# Make names less annoying
def quick_call(obj, name):
    obj.__name__ = name
    return obj
DO = quick_call(DictObject, 'DO')
O = quick_call(Namespace, 'O')
