from poly.common import *
from poly.expr import *
from poly.prim import prim_table
from poly.reader import read_expr

class ModuleError(PolyError):
    def __init__(self, error):
        self.message = "Module couldn't be loaded: {}".format(error.message)
        self.error = error

class Node:
    def __init__(self, name):
        self.name = name
        self.env = Env(prim_table)

        self.refs = {}
        self.next_ref_id = 0

    def names(self):
        return self.env.table.keys()

    def read(self, s):
        return read_expr(s)

    def make_ref(self):
        ref_id = self.next_ref_id
        self.next_ref_id += 1

        self.refs[ref_id] = None
        return Ref(ref_id)

    def get_ref(self, ref_id):
        if ref_id in self.refs:
            return self.refs[ref_id]
        else:
            raise UndefinedRefError(ref_id)

    def set_ref(self, ref_id, val):
        if ref_id in self.refs:
            self.refs[ref_id] = val
        else:
            raise UndefinedRefError(ref_id)

    def eval(self, expr):
        return expr.eval(self, self.env)

    def load_module(self, path, prefix=None):
        with open(path, "r") as f:
            s = f.read()

        try:
            expr = self.read(s)
            module = self.eval(expr)
        except PolyError as e:
            raise ModuleError(e)

        name, defs = module.data

        if prefix is None:
            prefix = name + "/"

        for name, func in defs.items():
            full_name = prefix + name
            self.env[full_name] = func

    def exit(self):
        return
