import sys

from bottle import run, get, post, request, response, hook, static_file

from poly.common import *
from poly.node import *
from poly.reader import ReaderError

node = Node("main")
node.load_module("prelude.poly", "")

def server_main(args):
    config = {
        "host": "0.0.0.0",
        "port": 8000,
        "debug": True
    }

    try:
        config["port"] = int(args[0])
    except:
        pass

    run(**config)

class ServerError(Exception):
    def __init__(self, message):
        self.message = message

@get("/")
def repl():
    return static_file("repl.html", root="static")

@get("/favicon.ico")
def get_favicon():
    return static_file("favicon.ico", root="static")

@get("/img/<path:path>")
def get_img(path):
    return static_file(path, root="static/img")

@get("/css/<path:path>")
def get_css(path):
    return static_file(path, root="static/css")

@get("/js/<path:path>")
def get_js(path):
    return static_file(path, root="static/js")

@get("/completions")
def completions():
    name = request.query.get("name")

    if name is None:
        err = ServerError("No input given")
        return error_resp(err)

    if len(name) <= 2:
        err = ServerError("Input must be longer than 2 characters")
        return error_resp(err)

    has_prefix = lambda s: s.startswith(name)
    matches = filter(has_prefix, node.names())
    matches = sorted(matches)

    return values_resp(matches)

@post("/eval")
def eval():
    s = request.forms.get("input")

    if s is None:
        err = ServerError("No input given")
        return error_resp(err)

    s = s.strip()

    try:
        expr = node.read(s)
    except ReaderError as e:
        return error_resp(e)

    try:
        val = node.eval(expr)
    except PolyError as e:
        return error_resp(e)

    return expr_resp(val)

def expr_resp(val):
    return {
        "type": "expr",
        "value": str(val)
    }

def values_resp(vals):
    return {
        "values": list(vals)
    }

def error_resp(error):
    return {
        "type": "error",
        "message": error.message
    }

if __name__ == "__main__":
    server_main(sys.argv[1:])
