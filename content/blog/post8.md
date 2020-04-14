Title: Automating the Binding Process in Cython
Date: 2020-04-13 12:20
Category: Python, Cython
Tags: Python, Cython, Binding

Summary: We discuss an approach towards automating the writing of Cython bindings


Cython is a wonderful tool for writing Python bindings.  It gives the developer a
tremendous amount of control over both code performance and semantics in a language
that is a superset of Python. It's no surprise much of the Scientific Python
ecosystem uses Cython to C and C++ libraries.

However, in this article, I want to discuss one of common pain points of
using Cython and an approach I'm currently working on to alleviate some of this pain.
This pain point is the shear amount of code one needs to write in Cython. Consider
the following dummy C++ class

```
#foo.hpp

class Foo {
    Foo(int a);
    int foo_meth(int b);
}

```

In order to build cython bindings for this class one would need write, at a minimum,
one pxd file for the c-level declaration

```cython
# _foo.pxd
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

So you can see that 3 lines from a C++ file became ~12 lines of Cython.  This
isn't a major problem for small C or C++ libraries, but for large libraries with
1000's of interface files, writing Cython bindings for the entire library becomes  
a colossal task.

A second problem that arises is when a C or C++ library is under heavy active development.
Public interfaces may change significantly from one release to the next leaving
your nice Cython bindings completely obsolete.  Like Sysphus, you're plagued with the
eternal task of keeping your bindings up to date with the latest release.

   
