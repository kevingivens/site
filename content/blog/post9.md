Title: Automating the Binding Process in Cython, Part 2
Date: 2020-04-20 19:10
Category: Cython
Tags: Python, Cython, Binding

Summary: We continue to discuss an approach towards automating the writing of Cython
bindings. We focus on generating pyx files.

### Part 2, Overview

In the previous post, I discussed generating pxd files (Cython C-level declarations)
from C header files using pycparser.  In this post, I want to explore using Cython's
own parser to generate the corresponding python wrapper classes and functions in a
pyx files.

## Using Cython's Parser

Cython's parser in written in Python.  It's fairly straight-forward to use, though
not terribly well documented.  Like all languages, there is a hierarchy of types
each represented as a node type.  Cython code is then parsed into a tree of
nodes to form an abstract syntax tree that can be traversed to generate new code.

## Handling Includes

Includes should be one of the simple aspects of the parser.  However, there is
one subtlety that needs to be addressed.  In particular, Cython has a convention
whereby any pyx file, say `foo.pyx`, with automatically include any C declarations
from a pxd file with the same name, e.g. `foo.pxd`, at compile time.  This can
cause a name clash if we wish to give our python classes and methods the same
name in Python as the have in the underlying C library.

One approach to avoiding clashes is to first name the pxd file `_foo.pxd` to prevent it from
being automatically included in `foo.pyx`.  Then rename the c-decelations    

## Python Class Lifetime Management


## Wrapping Functions

## Python Protocols and Special Methods

## Final Words

In my next post, I will revisit this process for C++.  In particular, I'll use libClang to parse C++ header flies.
