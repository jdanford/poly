from logging import captureWarnings

from rply import LexerGenerator, ParserGenerator
from rply.errors import LexingError, ParsingError

from poly.common import *
from poly.expr import *

captureWarnings(True)

class ReaderError(PolyError):
    def __init__(self, input, tokens=False):
        self.message = "Can't read '{}'".format(input)
        self.input = input
        self.tokens = []

        if tokens:
            self.tokens = get_tokens(input)
            self.message += " (tokens={})".format(self.tokens)

tokens = {
    "LPAREN": r"\(",
    "RPAREN": r"\)",
    "LSQUARE": r"\[",
    "RSQUARE": r"\]",
    "LBRACE": r"\{",
    "RBRACE": r"\}",
    "DOT": r"\.",
    "UNDER": r"_",
    "SQUOTE": r"'",
    #"COMMENT": r"!",
    "LINECOMMENT": r";[^\n]*",
    "NUMBER": r"[0-9]+(\.[0-9]+)?|0x[0-9a-fA-F]+",
    "STRING": r"\"(\\\"|[^\"])*\"",
    "IDENT": SAFE_IDENT,
    "RAWIDENT": r"`(\\`|[^`])+`",
    "SYMBOL": SAFE_SYMBOL,
    "RAWSYMBOL": r"#`(\\`|[^`])+`",
}

lg = LexerGenerator()

for rule, regex in tokens.items():
    lg.add(rule, regex)

lg.ignore(r"[\s,]+")

token_names = list(tokens.keys())
pg = ParserGenerator(token_names, cache_id="poly_reader")

@pg.production("main : expr")
def main(p):
    return p[0]

@pg.production("exprs : expr")
def exprs_one(p):
    return [p[0]]

@pg.production("exprs : expr exprs")
def exprs_many(p):
    return [p[0]] + p[1]

# @pg.production("expr : expr COMMENT expr")
# def expr_then_comment(p):
#     return p[0]

# @pg.production("expr : COMMENT expr expr")
# def comment_then_expr(p):
#     return p[2]

@pg.production("expr : _comment")
def exprs_comment(p):
    return p[0]

@pg.production("_comment : expr LINECOMMENT")
def expr_then_linecomment(p):
    return p[0]

@pg.production("_comment : _comment LINECOMMENT")
def comment_then_linecomment(p):
    return p[0]

@pg.production("expr : UNDER")
def expr_blank(p):
    return blank

@pg.production("expr : IDENT")
def expr_var(p):
    name = p[0].getstr()
    return Var(name)

@pg.production("expr : RAWIDENT")
def expr_raw_ident(p):
    body = p[0].getstr()[1:-1]
    name = tick_string(body)
    return Var(name)

@pg.production("expr : SQUOTE expr")
def expr_quote(p):
    return Quote(p[1])

@pg.production("expr : atom")
def expr_atom(p):
    return p[0]

@pg.production("expr : coll")
def expr_coll(p):
    return p[0]

@pg.production("atom : NUMBER")
def atom_number(p):
    s = p[0].getstr()

    if s[0:2] == "0x":
        rest = s[2:]
        n = int(rest, 16)
        return Int(n)

    return read_number(s)

def read_number(s):
    try:
        n = int(s)
        expr = Int(n)
    except ValueError:
        f = float(s)
        expr = Float(f)

    return expr

@pg.production("atom : SYMBOL")
def atom_symbol(p):
    name = p[0].getstr()[1:]
    return Symbol(name)

@pg.production("atom : RAWSYMBOL")
def atom_raw_symbol(p):
    body = p[0].getstr()[2:-1]
    name = tick_string(body)
    return Symbol(name)

@pg.production("atom : STRING")
def atom_string(p):
    body = p[0].getstr()[1:-1]
    s = dquote_string(body)
    return String(s)

@pg.production("lbrack : LPAREN")
def lbrack_paren(p):
    return p[0]

@pg.production("lbrack : LSQUARE")
def lbrack_square(p):
    return p[0]

@pg.production("rbrack : RPAREN")
def rbrack_paren(p):
    return p[0]

@pg.production("rbrack : RSQUARE")
def rbrack_square(p):
    return p[0]

@pg.production("coll : lbrack rbrack")
def coll_nil(p):
    return nil

@pg.production("coll : lbrack exprs rbrack")
def coll_list(p):
    exprs = p[1]
    return make_list(exprs, nil)

@pg.production("coll : lbrack exprs DOT expr rbrack")
def coll_dotted_list(p):
    exprs = p[1]
    tail = p[3]
    return make_list(exprs, tail)

@pg.production("coll : LBRACE RBRACE")
def coll_empty_map(p):
    return Map()

@pg.production("coll : LBRACE exprs RBRACE")
def coll_map(p):
    return Map.from_exprs(p[1])

lexer = lg.build()
parser = pg.build()

def get_tokens(s):
    stream = lexer.lex(s)
    tokens = []

    while True:
        token = stream.next()

        if token is None:
            break

        tokens.append((token.name, token.value))

    return tokens

def read_expr(s):
    try:
        token_stream = lexer.lex(s)
        expr = parser.parse(token_stream)
    except LexingError:
        raise ReaderError(s)
    except ParsingError:
        raise ReaderError(s, tokens=True)

    return expr
