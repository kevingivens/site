Title: Automating the Binding Process in Cython
Date: 2020-04-20 19:10
Category: Cython
Tags: Python, Cython, Binding

Summary: We discuss an approach towards automating the writing of Cython bindings

### Part 1, Overview

Cython is a wonderful tool for writing Python bindings.  It gives the developer a
tremendous amount of control over both code performance and semantics in a language
that is a superset of Python. It's no surprise much of the Scientific Python
ecosystem uses Cython to wrap C and C++ libraries.

However, in this post, I want to discuss one of the common pain points of Cython as
well an approach I'm currently working on to alleviate some of this pain.
The pain point I'm focusing on is the shear amount of code one needs to write in
Cython. Consider the following dummy C++ class

```cpp
// foo.hpp

class Foo {
    Foo(int a);
    int foo_meth(int b);
}
```

In order to build cython bindings for this class, one would need write, at a minimum,
one pxd file for the c-level declaration

```cython
# foo.pxd

cdef cppclass Foo:
    Foo(int a)
    int foo_meth(int b)

```

and one pyx file for the python class that wraps the C++ classes

```cython
# foo.pyx

cdef class Foo:

    cdef shared_ptr[_foo.Foo] _thisptr

    def __cinit__(self, a):
        self._thisptr = _foo.Foo(<int>a)

    def __dealloc__(self):
        if self._thisptr == NULL:
            self._thisptr.reset()

    def foo_meth(b):
        return self._thisptr.foo_meth(<int>a)

```

So you can see that 3 lines from a C++ file becomes ~12 lines of Cython.  This
isn't a major problem for small C or C++ libraries, but for large libraries with
1000's of interface files, writing Cython bindings for the entire library becomes
a colossal task.

A second problem can arise when a C or C++ library is under heavy active development.
Public interfaces may change significantly from one release to the next rendering your
hard-fought Cython bindings obsolete.  Like Sisyphus, you're plagued with the
eternal task of keeping your bindings up to date with the latest release.

One natural approach to resolving this dilemma to write a computer program
that automatically generates these bindings for you, "on the fly", every time there is a
new release of the underlying C or C++ library.  It's this approach I want to
discuss in here.

The essence of the idea is familiar for anyone who has studied compilers. If you
want to transform data (in this case, code) from one language (C/C+) to another (Cython)
you need a parser.  The work flow is to first translate the C/C++ source code into an
[abstract syntax tree](https://en.wikipedia.org/wiki/Abstract_syntax_tree) and
then to walk the tree and generate the transformed Cython code. So all we need in
order to give this approach a try is a C/C++ parser.  Know any good ones?

Just kidding, sort of.  Until recently, the only C/C++ parser in the open source
world was buried inside GCC along with linkers, Fortran parsers, and various other
goodies. Thankfully, this situation has improved with the LLVM project.  Clang is
production quality C family compiler whose parser is accessible in python through
the [libClang](https://clang.llvm.org/doxygen/group__CINDEX.html) bindings. The
story for C code, is even better.  There is an open source C parser written in pure
python called [pycparser](https://github.com/eliben/pycparser).

We can actually take this parsing approach one step further.  We can use the
C/C++ parsers to translate source code into C-level declarations in pxd files
and then use Cython's own parser to translate from pxd files into pyx files.  This
latter step is the approach taken by the [autowrap](https://github.com/uweschmitt/autowrap)
project.  A schematic overview of the process is given below

![png]({attach}post8_files/cython_parse.png)


## Pycparser

Pycparser is a C parser written in pure python. We can use it to parse C header
files and generate corresponding pxd files.  For the purpose of this post, we'll
use an example C file from the [c-algorithms library](https://github.com/fragglet/c-algorithms)
In particular, we'll focus on its implementation of a [trie](https://en.wikipedia.org/wiki/Trie)
data structure (trie.h), annotated in the snippet below:

```cpp
// trie.h

typedef struct _Trie Trie;

typedef void *TrieValue;

Trie *trie_new(void);

void trie_free(Trie *trie);

int trie_insert(Trie *trie, char *key, TrieValue value);
...
```

The idea is to use pycparser to translate this to the equivalent cython declarations
in a pxd file.  The generated pxd file would look like this:

```cython
# trie.pxd

cdef extern from "c-algorithms/src/trie.h":
    ctypedef struct Trie:
        pass

    ctypedef void *TrieValue

    Trie *trie_new()
    void trie_free(Trie *trie)

    int trie_insert(Trie *trie, char *key, TrieValue value)
    ...

```

So the translation consists of the following:

- placing all statements inside a `cdef extern` block
- `typedef` goes to `ctypedef`
- trailing `;` is removed from each statement
- `typedef struct` goes to `pass` (skipped implementation)
- `trie_new(void)` has `void` removed


## AST

These translation are implemented by walking a intermediate data representation
known as an abstract syntax tree (AST).  Each node in the tree is "visited" by a
corresponding visit function.  The AST for this example looks like the following:

![png]({attach}post8_files/ast.jpeg)

In order to walk the AST, I wrote a Cython generator class.  This is slight modification of
the C generator that comes with the pycparser release.  Take a look at my [github](https://github.com/kevingivens/Blog)
for more details. The idea is to provide a `visit_foo` method for each node type that
generates the correct Cython implemenation code. Some highlights from the generator are given below

```python
def visit_Typedef(self, n):
    s = 'c' # prepend 'typedef' with 'c'
    if n.storage: s += ' '.join(n.storage) + ' '
    # handle typedef struct definition
	if type(n.type) == c_ast.TypeDecl and type(n.type.type) == c_ast.Struct:
        s += self._handle_typedef_struct(n.type)
    else:
        s += self._generate_type(n.type)
    return s

def visit_ParamList(self, n):
    ''' return '' if 'void' is only argument
	'''
    param_list = ', '.join(self.visit(param) for param in n.params)
    if param_list == 'void':
        return ''
	else:
	    return param_list

```

In my next post, I will discuss how to use the Cython parser itself to parse pxd files and generate pyx files.
