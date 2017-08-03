import sys
from string import whitespace

from clint.textui import puts, indent, colored

from poly.common import *
from poly.node import *

def repl_main(args):
    repl = Repl("repl")
    repl.run()

class UndefinedCommandError(PolyError):
    def __init__(self, command):
        self.message = "Undefined command '{}'".format(command)

class Repl:
    def __init__(self, name, in_prompt=None, out_prompt=None):
        self.node = Node(name)

        if in_prompt is None:
            in_prompt = ">> "

        self.in_prompt = in_prompt

        if out_prompt is None:
            out_prompt = "\n" + " " * len(in_prompt)

        self.out_prompt = out_prompt

        try:
            self.node.load_module("prelude.poly", "")
        except ModuleError as e:
            self.print_error(e)

    def run(self):
        self.print_banner("Poly 0.0")

        while True:
            s, is_command = self.get_input()

            if is_command:
                try:
                    exit = self.handle_command(s)
                except UndefinedCommandError as e:
                    self.print_error(e)
                    exit = False

                if exit:
                    break
                else:
                    continue

            try:
                expr = self.node.read(s)
                self.eval_and_print(expr)
            except PolyError as e:
                self.print_error(e)

    def eval_and_print(self, expr0):
        expr1 = self.node.eval(expr0)
        self.print_result(expr1)

        self.node.env.table["$"] = expr1

    def handle_command(self, cmd):
        if cmd in ["q", "quit"]:
            return True
        elif cmd[0] == " ":
            self.print_warning(cmd[1:])
        else:
            raise UndefinedCommandError(cmd)

        return False

    def get_input(self):
        while True:
            try:
                prompt = self.in_prompt
                puts(prompt, newline=False)

                s = input().strip()

                if empty_space(s):
                    continue
                elif s[0] == ":":
                    return s[1:], True
                else:
                    return s, False
            except (EOFError, KeyboardInterrupt):
                puts()
                return "quit", True

    def print_banner(self, s, width=72):
        line = "-" * width

        puts(line)
        puts(s)
        puts(line + "\n")

    def print_result(self, expr):
        prompt = colored.blue(self.out_prompt)
        puts(prompt + str(expr) + "\n")

    def print_str(self, s):
        puts(s)

    def print_warning(self, s):
        sign = colored.yellow("Warning: ")
        puts(sign + s + "\n")

    def print_error(self, e):
        sign = colored.red("Error: ")
        puts(sign + e.message + "\n")

def empty_space(s):
    if len(s) == 0:
        return True

    for c in s:
        if s in whitespace:
            return True

    return False

if __name__ == "__main__":
    repl_main(sys.argv[1:])
