import operator
from collections import OrderedDict

from poly.expr import *

prim_table = {}

def prim(name):
    def dec(func):
        prim_table[name] = Prim(func)
        return func

    return dec

def wprim(name):
    def dec(func):
        prim_table[name] = Wrapped(Prim(func))
        return func

    return dec

def math(name):
    def dec(func):
        def wrapped(node, env, expr):
            exprs = list(expr.values())
            vals, wrapper = unwrap_nums(exprs)
            res = func(vals, wrapper)
            return res

        prim_table[name] = Wrapped(Prim(wrapped))
        return wrapped

    return dec

@prim("module")
def _module(node, env, expr):
    defs = OrderedDict()

    module_name = expr.head.name
    ls = expr.tail

    while ls != nil:
        name = ls.head.name
        func = ls.tail.head
        ls = ls.tail.tail

        defs[name] = func

    names = list(defs.keys())
    menv = env.with_forwards(names)

    for name in names:
        expr = defs[name]
        val = expr.eval(node, menv)

        defs[name] = val
        menv.set_forward(name, val)

    return NativeValue(module_name, defs)

@wprim("hash")
def _hash(node, env, expr):
    (val,) = expr.values()
    h = hash(val)
    return Int(h)

@wprim("cons")
def _cons(node, env, expr):
    head, tail = expr.values()
    return Cons(head, tail)

@wprim("join")
def _join(node, env, expr):
    l1, l2 = expr.values(Cons, Cons)
    values = list(l1.values()) + list(l2.values())
    return make_list(values)

@wprim("fmt")
def _fmt(node, env, expr):
    s0 = expr.head
    l = expr.tail
    fs = s0.value
    s1 = fs.format(*l.values())
    return String(s1)

@wprim("eval")
def _eval(node, env, expr):
    expr0, env0 = expr.values(Expr, Env)
    return expr0.eval(node, env0)

@prim("op")
def _op(node, env, expr):
    pat, epat, body = expr.values()
    return Operative(pat, epat, body, env)

@wprim("op*")
def _op__star(node, env, expr):
    pat, epat, body, env0 = expr.values(Expr, Expr, Expr, Env)
    return Operative(pat, epat, body, env0)

@wprim("wrap")
def _wrap(node, env, expr):
    (func,) = expr.values(Func)
    return Wrapped(expr.head)

@prim("let")
def _let(node, env, expr):
    env = env.clone()
    assocs, body = expr.values(Cons, Expr)

    bindings = []

    while assocs != nil:
        pair = assocs.head
        assocs = assocs.tail

        pat = pair.head
        expr = pair.tail.head
        bindings.append((pat, expr))

    for pat, expr in bindings:
        val = expr.eval(node, env)
        penv = pat.unify(val)
        env += penv

    return body.eval(node, env)

@prim("match")
def _match(node, env, expr):
    head, cases = expr.values(Expr, Cons)
    val = head.eval(node, env)

    pairs = []

    while cases != nil:
        pair = cases.head
        cases = cases.tail

        pat = pair.head
        expr = pair.tail.head
        pairs.append((pat, expr))

    for pat, expr in pairs:
        try:
            penv = pat.unify(val)
        except MatchError:
            continue

        fenv = env + penv
        return expr.eval(node, fenv)

@wprim("show")
def _show(node, env, expr):
    (val,) = expr.values()
    s = str(val)
    return String(s)

@wprim("print-string")
def _print_string(node, env, expr):
    (val,) = expr.values()

    if isinstance(val, String):
        print(val.value)
    else:
        raise InvalidTypeError(val, String)

@wprim("set*")
def _set__star(node, env, expr):
    head, expr0 = expr.values()
    name = head.name
    node.env[name] = expr0

@wprim("ref/new")
def _ref__new(node, env, expr):
    (expr1,) = expr.values()
    ref = node.make_ref()
    node.set_ref(ref.id, expr1)

    return ref

@wprim("ref/get")
def _ref__get(node, env, expr):
    (ref,) = expr.values(Ref)
    return node.get_ref(ref.id)

@wprim("ref/set!")
def _ref__set(node, env, expr):
    ref, expr1 = expr.values(Ref, Expr)
    node.set_ref(ref.id, expr1)

@math("+")
def _add(vals, wrapper):
    x = 0

    for v in vals:
        x += v

    return wrapper(x)

@math("-")
def _sub(vals, wrapper):
    x = 0

    if len(vals) >= 2:
        x = vals[0]
        vals = vals[1:]

    for v in vals:
        x -= v

    return wrapper(x)

@math("*")
def _mul(vals, wrapper):
    x = 1

    for v in vals:
        x += v

    return wrapper(x)

@math("/")
def _div(vals, wrapper):
    x = 1.0

    if len(vals) >= 2:
        x = vals[0]
        vals = vals[1:]

    for v in vals:
        x /= float(v)

    return Float(x)
