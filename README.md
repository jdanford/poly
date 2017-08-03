# Poly

Poly is a neat little gal who stands on the shoulders of giants:

- [Kernel](http://web.cs.wpi.edu/~jshutt/kernel.html)
- Haskell
- Python

## Features

- [fexprs](https://en.wikipedia.org/wiki/Fexpr) (≈ first-class macros)
- pattern matching
- immutable data structures
- built-in web REPL

## Requirements

- Python 3.3+
- `virtualenv`
- `rlwrap` (optional, for command line REPL)

## Install it

Clone the repo

    git clone https://github.com/jdanford/poly.git

Make a virtualenv

    virtualenv -p python3.3 poly

Activate the virtualenv

    cd poly
    source bin/activate

Install required packages

    pip install -r requirements.txt

Run the REPL from the command line

    ./run repl

...or a web browser

    ./run server [port]

## Hack on it

Run `static/build-assets` to recompile the CoffeeScript and LESS files
