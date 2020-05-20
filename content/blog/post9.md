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

As a reminder from the last post, we are generating Python bindings for a C
implementation of a trie data structure from the [c-algorithms library](https://github.com/fragglet/c-algorithms)
(Incidentally, code from this same library is used as an example in the official Cython
[documentation](https://cython.readthedocs.io/en/latest/src/tutorial/clibraries.html)).  
There's a lot of overlap between that documentation of some of the topics discussed here).

Cython's parser in written in Python.  It's fairly straight-forward to use, though
not terribly well documented.  As with any conventional parser, there is a hierarchy
of types each represented as a node in an abstract syntax tree.  The parser reads
Cython code in `pyx`, `pxd`, or `pxi` files and generates C code that implements
the CPython API.   

Our approach, borrowed from the autowrap [project](https://github.com/uweschmitt/autowrap),  
is to use Cython's `pxd` reading capabilities to generate `pyx` files. After all,
for most Cython projects, one tries to maintain some type of consistent standard
when implementing wrapper functions and objects.  Using a parser just implements
these standards automatically.

### Compiler Pipeline

Now for some code.  Cython's pxd parser can be accessed programatically.  In the snippet below,
the we parse a pxd file from the command line and return an AST.


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
This pipeline is like a regular compiler pipeline through which phases of data
transformations occur.  For our purposes, just walking the AST starting
from the root node.

Parsing our trie.pxd file from the previous post generates the following AST:

![png]({attach}post9_files/trie_ast.png)

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

The C structs defined in the pxd files should be wrapped by Python classes, as these are
the closest language equivalent.  Ideally, the Python classes will manage the
lifetime of the corresponding C struct.  This means that the C struct will be
created when the Python is created and it will be destroyed and its memory
released when the Python object is destroyed.  In this way, the C struct is
`buried under the hood`, so the speak, and the Python class user is essentially
oblivious to its existence.

For our trie example, the python wrapper class looks like the following:


```cython
cimport _trie

cdef class Trie:

    cdef _trie.Trie* _this_ptr

    def __cinit__(self):
        self._this_ptr = _trie.trie_new()
        if self._this_ptr is NULL:
            raise MemoryError()

    def __dealloc__(self):
        if self._this_ptr is not NULL:
            _trie.trie_free(self._this_ptr)
```

This ensures that the lifetime of the underlying C Trie struct is tied to the lifetime
of the Python Trie class.

In order to build the Python wrapper class, our parser needs to identify all the
structs defined in the pxd file. It also needs to identify the `_new` and `_free`
functions associated with a given struct in order to link them with the constructors
and destructors in the Python class.    


## Wrapping Functions
Wrapping C functions is simple in principle.  The idea is to cast the Python
objects from the function signature into their nearest C equivalent type,   
then call the underlying C function via the internal pointer and finally convert any
returned C objects back to Python types.  Wrapping functions is essentially an exercise in
managing type conversions between C and Python.

However, in practice, this can be a difficult task for a compiler to achieve. For
instance, in our trie example the `insert` method has the following C signature

```c
int trie_insert(Trie *trie, char *key, TrieValue value);
```
as a reminder, TrieValue is a typedef of `void*`

So the type conversion is
| Python type | C type |
------------------------
|str  | char* |
|int  | int |
|object| void*|

a naive Python wrapper would look like the following

```cython
def insert(self, str key, value):
    cdef char* c_key = key.encode('UTF-8')
    return self._this_ptr.trie_insert(Trie *trie, c_key, <void*>value)

```

There are a few problems with this approach. The most obvious problem is the fact
the returned `int` is not really meant to be an integer, per se.  It's an int
from a C function call indicating failure by a 0 and success by a positive value.
Clearly, a parser just looking at the C signature cannot distinguish between an
int of this type and an regular int.

Cython provides an alternative type, `bint`, as in binary int, that can be used
for these types of function calls.  A `bint` autoconverts to a Python `bool`
instead of an `int`.  So for our pxd parser to pick it up, we would have to
manually update our pxd file from

```c
int trie_insert(Trie *trie, char *key, TrieValue value)
```   
to
```c
bint trie_insert(Trie *trie, char *key, TrieValue value)
```

The returned `bint`'s value should be checked and exception should be raised if it
is false.  So am improved wrapper look like the following

```cython
def insert(self, str key, value):
    cdef char* c_key = key.encode('UTF-8')
    if not _trie.trie_insert(self._thisptr, c_key, <void*>value):
        raise MemoryError()
```

## Python Protocols and Special Methods

As an easier wrapping example, the length of the `trie` struct can be determined via the
following function

```c
unsigned int trie_num_entries(Trie *trie);
```

Our python wrapper is simply

```cython
def num_enties(self):
    return _trie.trie_num_entries(self._this_ptr)
```

Clearly, Python users would expect a `__len__()` special method instead of `num_entries()`.
We can either allow users to adjust the function name manually after generating the pyx file
or directly map `num_enties` to `__len__` in the pxd parser. We'll use a direct mapping
for now but it's by no means a general solution.  

So our length method would look like the following

```cython
def __len__(self):
    return _trie.trie_num_entries(self._this_ptr)
```

This problem can emerge for any C functions that implements Python protocol functionality,
such as `__get__()`, `__set__()`, ` __getitem__(key)`, `__setitem__(key, value)`

## Final Words

There's much more work to do on the pxd files.  For

In my next post, I will revisit this process for C++.  In particular, I'll use
libClang to parse C++ header files.  See you next time.
