import re
from itertools import chain, repeat

from poly.common import *

class MatchError(PolyError):
    def __init__(self, lexpr, rexpr):
        self.message = "Can't match {} with {}".format(lexpr, rexpr)
        self.lexpr = lexpr
        self.rexpr = rexpr

class UndefinedError(PolyError):
    def __init__(self, name):
        self.message = "Undefined var {}".format(name)
        self.name = name

class UndefinedRefError(PolyError):
    def __init__(self, id):
        self.message = "Undefined ref {}".format(id)
        self.id = id

class CantEvalError(PolyError):
    def __init__(self, expr):
        self.message = "Can't evaluate {}".format(expr)
        self.expr = expr

class CantApplyError(PolyError):
    def __init__(self, expr):
        self.message = "Can't apply {}".format(expr)
        self.expr = expr

class DuplicateKeyError(PolyError):
    def __init__(self, key):
        self.message = "Duplicate key {}".format(key)
        self.key = key

class ImproperListError(PolyError):
    def __init__(self, expr):
        self.message = "Improper list {}".format(expr)

class InvalidTypeError(PolyError):
    def __init__(self, expr, typ):
        self.message = "{} must be of type {}".format(expr, typ.__name__)
        self.expr = expr
        self.type = typ

class Expr:
    def eval(self, node, env):
        return self

    def apply(self, node, env, expr):
        raise CantApplyError(self)

    def unify(self, other):
        if self == other:
            return Env()
        else:
            raise MatchError(self, other)

    def lvars(self):
        return set()

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        s = str(self)
        h = hash(s)
        return h

class Nil(Expr):
    _ORDER = 0

    def eval_list(self, node, env):
        return self

    def values(self):
        return iter([])

    def __str__(self):
        return "()"

nil = Nil()

class Blank(Expr):
    _ORDER = 1

    def __str__(self):
        return "_"

    def eval(self, node, env):
        raise CantEvalError(self)

    def unify(self, other):
        return Env()

blank = Blank()

class Var(Expr):
    _ORDER = 2

    def __init__(self, name):
        self.name = name

    def __str__(self):
        safe = re.match(SAFE_IDENT, self.name)

        if safe:
            return self.name
        else:
            return "`{}`".format(self.name)

    def eval(self, node, env):
        return env[self.name]

    def unify(self, other):
        name = self.name
        return Env({name: other})

    def lvars(self):
        return {self.name}

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.name == other.name

    def __hash__(self):
        return hash(self.name) + self._ORDER

class Atom(Expr):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            (self is other or self.value == other.value)

    def __hash__(self):
        return hash(self.value) + self._ORDER

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.value < other.value
        else:
            return self._ORDER < other._ORDER

class Num(Atom):
    def __str__(self):
        return str(self.value)

class Int(Num):
    _ORDER = 3

class Float(Num):
    _ORDER = 4

def largest_num_type(exprs):
    for expr in exprs:
        if isinstance(expr, Float):
            return Float

    return Int

def unwrap_nums(exprs):
    def num_value(num):
        if isinstance(num, Num):
            return num.value
        else:
            raise InvalidTypeError(num, Num)

    typ = largest_num_type(exprs)
    vals = list(map(num_value, exprs))
    return vals, typ

class Symbol(Atom):
    _ORDER = 5

    def apply(self, node, env, expr):
        body = expr.eval_list(node, env)
        return Cons(self, body)

    def __str__(self):
        name = self.value
        pat = SAFE_SYMBOL[1:]
        safe = re.match(pat, name)

        if safe:
            return "#" + name
        else:
            return "#`{}`".format(name)

def dquote_string(s):
    py_expr = '"' + s + '"'
    return eval(py_expr)

def tick_string(s):
    return s.replace(r"\`", "`")

class String(Atom):
    _ORDER = 6

    def __init__(self, value=None):
        if value is None:
            value = ""

        self.value = value

    def __str__(self):
        s = repr(self.value)[1:-1]
        s = s.replace('"', r'\"').replace(r"\'", "'")

        return '"' + s + '"'

class Ref(Expr):
    _ORDER = 7

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "(ref {})".format(self.id)

class Quote(Expr):
    _ORDER = 8

    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return "'" + str(self.expr)

    def eval(self, node, env):
        return self.expr

    def __eq__(self, other):
        return isinstance(other, Quote) and self.expr == other.expr

    def __hash__(self):
        return hash(self.expr) + self._ORDER

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.expr < other.expr
        else:
            return self._ORDER < other._ORDER

class Env(Expr):
    _ORDER = 9

    def __init__(self, table=None, forwards=None):
        if table is None:
            table = {}

        self.table = dict(table)

        if forwards is None:
            forwards = {}

        self.forwards = dict(forwards)

    def __getitem__(self, name):
        if name in self.table:
            return self.table[name]

        if name in self.forwards:
            val = self.forwards[name][0]

            if val is not None:
                self.table[name] = val
                del self.forwards[name]
                return val

        raise UndefinedError(name)

    def __setitem__(self, name, val):
        if name in self.forwards:
            del self.forwards[name]

        self.table[name] = val

    def set_forward(self, name, val):
        if name in self.forwards:
            self.forwards[name][0] = val
        else:
            raise UndefinedError(name)

    def __add__(self, other):
        env = self.clone()
        env += other
        return env

    def __iadd__(self, other):
        for name, val in other.table.items():
            self[name] = val

        return self

    def clone(self):
        return Env(self.table, self.forwards)

    def with_forwards(self, names):
        env = self.clone()

        for name in names:
            env.forwards[name] = [None]

        return env

    def __str__(self):
        return "(env ...)"

class Func(Expr):
    _ORDER = 10

class Operative(Func):
    def __init__(self, pat, epat, body, env):
        self.pat = pat
        self.epat = epat
        self.body = body
        self.env = env.clone()

    def apply(self, node, env, expr):
        pat_env = self.pat.unify(expr)
        dyn_env = env.clone()
        epat_env = self.epat.unify(dyn_env)
        func_env = self.env + pat_env + epat_env

        return self.body.eval(node, func_env)

    def __str__(self):
        return "(op {} {} ...)".format(str(self.pat),
                                       str(self.epat))

class Wrapped(Func):
    def __init__(self, func):
        self.func = func

    def apply(self, node, env, expr):
        expr1 = expr.eval_list(node, env)
        return self.func.apply(node, env, expr1)

    def __str__(self):
        return "(wrap {})".format(str(self.func))

class Prim(Func):
    def __init__(self, func):
        self.func = func

    def apply(self, node, env, expr):
        val = self.func(node, env, expr)

        if val is None:
            return Nil()
        elif isinstance(val, Expr):
            return val
        else:
            return NativeValue(val)

    def __str__(self):
        return "(prim ...)"

class Coll(Expr):
    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return False
        else:
            return self._ORDER < other._ORDER

class Cons(Coll):
    _ORDER = 11

    def __init__(self, head, tail):
        self.head = head
        self.tail = tail

    def __str__(self):
        expr = self
        strs = []

        while True:
            head_str = str(expr.head)
            strs.append(head_str)

            if expr.tail == nil:
                break
            elif isinstance(expr.tail, Cons):
                expr = expr.tail
            else:
                tail_str = str(expr.tail)
                strs += [".", tail_str]
                break

        return wrap("(", ")", strs)

    def unify(self, other):
        if isinstance(other, Cons):
            return self.head.unify(other.head) + \
                self.tail.unify(other.tail)
        else:
            raise MatchError(self, other)

    def values(self, *types):
        cons = self
        types = chain(types, repeat(Expr))

        for typ in types:
            value = cons.head

            if typ is not None and not isinstance(value, typ):
                raise InvalidTypeError(value, typ)

            yield value

            if cons.tail == nil:
                return
            elif isinstance(cons.tail, Cons):
                cons = cons.tail
            else:
                raise ImproperListError(self)
                break

    def lvars(self):
        s = self.head.lvars()
        s.update(self.tail.lvars())

        return s

    def eval(self, node, env):
        head = self.head.eval(node, env)
        return head.apply(node, env, self.tail)

    def eval_list(self, node, env):
        exprs = []
        cons = self

        while True:
            exprs.append(cons.head)

            if cons.tail == nil:
                break
            elif isinstance(cons.tail, Cons):
                cons = cons.tail
            else:
                raise ImproperListError(self)
                break

        exprs1 = [expr.eval(node, env) for expr in exprs]
        return make_list(exprs1)

    def __eq__(self, other):
        return isinstance(other, Cons) and \
            self.head == other.head and \
            self.tail == other.tail

    def __hash__(self):
        h = 0
        cons = self

        while True:
            expr = cons.head
            h = add_hash(h, expr)

            if cons.tail == nil:
                break
            elif isinstance(cons.tail, Cons):
                cons = cons.tail
            else:
                h = add_hash(h, cons)
                break

        return h

def add_hash(h, x):
    return h * 31 + hash(x)

def make_list(exprs, tail=None):
    if tail is None:
        tail = nil

    cons = tail

    for expr in reversed(exprs):
        cons = Cons(expr, cons)

    return cons

class Map(Coll):
    _ORDER = 12

    def __init__(self, items=None):
        if items is None:
            items = {}

        self.items = items

    def keys(self):
        return sorted(self.items.keys())

    @classmethod
    def from_exprs(cls, exprs):
        items = {}
        keys = set()

        l = len(exprs)
        for i in range(0, l, 2):
            k = exprs[i]

            if k in keys:
                raise DuplicateKeyError(k)
            else:
                keys.add(k)

            v = exprs[i + 1]
            items[k] = v

        return cls(items)

    def __str__(self):
        strs = []

        for k in self.keys():
            v = self.items[k]
            strs += [str(k), str(v)]

        return wrap("{", "}", strs)

    def eval(self, node, env):
        items = {}

        for k, v in self.items.items():
            k1 = k.eval(node, env)
            v1 = v.eval(node, env)

            items[k1] = v1

        return Map(items)

    def __eq__(self, other):
        keys1 = set(self.items.keys())
        keys2 = set(other.items.keys())

        if keys1 == keys2:
            for k in keys1:
                if self.items[k] != other.items[k]:
                    return False
        else:
            return False

        return True

    def __hash__(self, other):
        h = 0

        for k in self.keys():
            v = self.items[k]

            h = add_hash(h, k)
            h = add_hash(h, v)

        return h

def wrap(l, r, strs):
    body = " ".join(strs)
    return l + body + r

class NativeValue(Expr):
    _ORDER = 13

    def __init__(self, *args):
        self.data = args

    def __str__(self):
        body = " ".join(map(repr, self.data))
        return "(native-value {})".format(body)
