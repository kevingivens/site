Title: Automating the Binding Process in Cython, Part 2
Date: 2020-04-27 19:10
Category: Cython
Tags: Python, Cython, Binding

Summary: We continue to discuss an approach towards automating the writing of Cython
bindings. We focus on generating pyx files.

### Part 2, Overview

In the previous [post]({attach}post8.md), I discussed generating pxd files (Cython C-level declarations)
from C header files using pycparser.  In this post, I want to explore using Cython's
own parser to generate the corresponding python wrapper classes and functions in a
pyx files.  As always, you can find the companion code to this post on my [github page](https://github.com/kevingivens/Blog)

## Using Cython's Parser

As a reminder from the last post, we are generating python bindings for a C implementation of a trie data
structure from the [c-algorithms library](https://github.com/fragglet/c-algorithms)
(Incidentally, code from this same library is used as an example in the official Cython
[documentation](https://cython.readthedocs.io/en/latest/src/tutorial/clibraries.html).  
There's a lot of overlap between that documentation of some of the topics discussed here).

Cython's parser in written in Python.  It's fairly straight-forward to use, though
not terribly well documented.  As with any conventional parser, there is a hierarchy of types
each represented as a node in an abstract syntax tree.  The parser reads Cython code in `pyx`, `pxd`, or `pxi` files
and generates C code that implements the CPython API.   

Our approach (or hack) is to use Cython's `pxd` reading capabilities to generate
`pyx` files.  After all, for most Cython projects, one tries to maintain some type of
 consistent standard when implementing wrapper functions and objects.  Using a parser
 just implements these standards automatically.

### Compiler Pipeline

Now for some code.  Cython's pxd parser can be accessed programatically.  In the snippet below,
the we parse a pxd file from the command line and return a AST.


```cython
from Cython.Compiler.CmdLine import parse_command_line
from Cython.Compiler.Main import create_default_resultobj, CompilationSource
from Cython.Compiler import Pipeline
from Cython.Compiler.Scanning import FileSourceDescriptor


def parse_pxd_file(path):
    options, sources = parse_command_line(["", path])

    path = os.path.abspath(path)
    basename = os.path.basename(path)
    name, ext = os.path.splitext(basename)

    source_desc = FileSourceDescriptor(path, basename)
    source = CompilationSource(source_desc, name, os.getcwd())
    result = create_default_resultobj(source, options)

    context = options.create_context()
    pipeline = Pipeline.create_pyx_pipeline(context, options, result)
    context.setup_errors(options, result)
    # root of the AST/parse tree
    root = pipeline[0](source)
```

We use the function `parse_command_line` to pass the source code located at `path` to
the Cython compiler with no compiler flags turned on. We then create a pxy compiler
`Pipeline` from a `CompilationSource` objects and a default `options context`.  
This pipeline is like a regular compiler pipeline through which optimizations are performed.  
For our purposes, we won't be doing any optimizations, just walking the AST starting
from the root node.

Parsing our trie.pxd file from the previous post generates the following AST



## Handling Includes

Includes should be one of the simple aspects of the parser.  However, there is
one subtlety that needs to be addressed.  In particular, Cython has a convention
whereby any pyx file, say `foo.pyx`, with automatically include any C declarations
from a pxd file with the same name, e.g. `foo.pxd`, at compile time.  This can
cause a name collision if we wish to give our Python classes and functions the same
name in Python as they have in the underlying C library.

One approach to avoiding name collisions is to first name the pxd file `_foo.pxd`
(add a leading underscore) to prevent it from being automatically included in `foo.pyx`.  
Then rename the imported C declarations with a leading underscore in the pyx file.  
This will prevent C and Python names from colliding in the pyx file.  


## Python Class Lifetime Management

C structs defined in pxd files, should be wrapped by Python classes, as these are the closest language equivalent.  
Ideally, the Python classes will manage the lifetime of the corresponding C struct.  This
means that the C struct will be created when the Python is created and it will be
destroyed and it's memory released when the Python object is destroyed.  In this way,
the C struct is `buried under the hood` so the speak, and the Python class user is essentially
oblivious to its existence.

To implement this approach for you trie example, 

## Wrapping Functions

## Python Protocols and Special Methods

## Final Words

In my next post, I will revisit this process for C++.  In particular, I'll use
libClang to parse C++ header files.  See you next time.
