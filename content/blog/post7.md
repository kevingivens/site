Title: Cython Bindings in PyQL
Date: 2020-03-10 12:20
Category: Coding
Tags: Cython

Summary: We review the general approach to Cython bindings in the PyQL library.

Recently, I've written a few posts, [here](https://github.com/kevingivens/blog/local-volatility-in-pyql.html) and
[here](https://github.com/kevingivens/blog/variance-swaps-in-pyql.html),
about my contributions to the PyQL library.  I thought I would take the opportunity
to review the general approach I've been using.  Although Cython is a fantastic tool
for writing Python bindings, its support for some of C++'s more advanced features (e.g. templates, smart pointers) is not
well documented online.  Hopefully these notes may be of use to Cython binding writers in general.

## The Basic Idea

The basic approach to writing bindings is to build wrapper functions around each
function in the compiled language use wish to export to users.  These wrapper functions manage
the input and output of data to the compiled functions, such that the user of the wrapper function can
safely ignore the details of the compiled language.  A schematic of this is given below[^1]

![png]({attach}post7_files/image_wrapper.jpg)  

[^1]: Credit: David Beazley Swig Master [Class](http://www.dabeaz.com/SwigMaster/SWIGMaster.pdf).

This approach applies to classes as well.  Let's take a look at a non-trivial example from PyQL to better understand the approach.

Consider the `CreditDefaultSwap` class from Quantlib(ql/instruments/creditdefaultswap.hpp). Its class definition looks like the following

```c++
class CreditDefaultSwap : public Instrument {

  CreditDefaultSwap(Protection::Side side,
                    Real notional,
                    Rate spread,
                    ...
                    const DayCounter& lastPeriodDayCounter = DayCounter(),
                    const bool rebatesAccrual = true);
  ...
  Protection::Side side() const;
  Real notional() const;
  ...
```

Where I've ignored most of the constructor arguments and class methods to simplify the discussion.

To expose this class in PyQL we first declare it in a cython definition file (.pxd) as follows

```cython
cdef extern from 'ql/instruments/creditdefaultswap.hpp' namespace 'QuantLib':

    cdef cppclass CreditDefaultSwap(Instrument):
        CreditDefaultSwap(Side side,
                          Real notional,
                          Rate spread,
                          ...                      
                          DayCounter& last_period_day_counter,
                          bool rebates_accrual
        )
        int side()
        Real notional()
        ...
```

For each of these declared classes we build a corresponding wrapper class in python. These python classes are defined in cython implementation file (.pyx) and are importable as python modules.

For the credit default swap, the python wrapper class is given below

```cython
cdef class CreditDefaultSwap(Instrument):

    def __init__(self,
                 Side side,
                 double notional,
                 double spread,
                 ...
                 DayCounter last_period_day_counter = Actual360(True),
                 bool rebates_accrual=True):
        """Credit default swap as running-spread only
        """

        self._thisptr = shared_ptr[_instrument.Instrument](
            new _cds.CreditDefaultSwap(
                side, notional, spread, deref(schedule._thisptr),
                payment_convention,
                deref(day_counter._thisptr), settles_accrual, pays_at_default_time,
                deref(protection_start._thisptr),
                shared_ptr[_cds.Claim](),
                deref(last_period_day_counter._thisptr),
                rebates_accrual)
        )

```

From this example we make the following observations:

- The constructor exposes Python objects to the user.  Simple types like double and bool
  are automatically converted by the cython compiler to the corresponding python type.
  More complex types such as DayCounter are defined elsewhere in the PyQL and imported to this file.

- The wrapper class manages the C++ class by means of a internal smart pointer
  ```
  self._thisptr = shared_ptr[_instrument.Instrument](new _cds.CreditDefaultSwap ...
  ```
  This pointer controls the lifetime of the corresponding C++ object along with
  any methods that are applied to it.  When the python object goes out of scope it
  resets the smart pointer which frees the memory that was allocated to the C++ object.

- Internal smart pointers are also used to pass C++ objects into the C++ constructor.  For instance
  ```
  deref(schedule._thisptr)
  ```
- Inheritance is managed by casting the smart pointer from Instrument down to CreditDefaultSwap.
  Most classes in PyQL have utility functions to perform this cast.  For the CDS, it's given below

```cython
cdef inline _cds.CreditDefaultSwap* _get_cds(CreditDefaultSwap cds):
    return <_cds.CreditDefaultSwap*>cds._thisptr.get()
```

This allows us to access the CDS's methods like the following snippet

```cython
@property
    def notional(self):
        return _get_cds(self).notional()

```

## Import Dilemma
The astute reader (you're all astute, I'm sure) will have noticed that both the C++ object and the Python object have the same name `CreditDefaultSwap`.  

This causes a name collision and a dilemma.  What's the best way to avoid such a collision? Some libraries take the approach of renaming the C/C++ object Foo_C or the Python object Foo_Py. PyQL takes a different approach.  

They first place the C++ objects in an underscored pxd file. For instance `_credit_default_swap.pxd'. They then import these objects into the pyx files as follows

```cython
import _credit_default_swap as _cds

```

The reason for the the underscore is that definition files with the same name as a pyx file, `credit_default_swap.pxd`, are automatically imported into `credit_default_swap.pyx`

This leads to the situation where there are three files for every one hpp file. This isn't ideal, but at least it's consistent and avoids having to rename C++ objects.

# Python Data Structures

One of the main reasons to prefer Cython over other binding tools is its flexibility.
PyQL takes advantage of this flexibility to make Quantlib more compatible with standard
Python data structures.  For example, Quantlib provides custom Date and Matrix objects
that are used throughout the library.  Python users would naturally prefer to use
`datetime.Date` and `NumPy` arrays instead of the custom objects.  PyQL provides utilities
for converting between these standard Python objects.

Numpy arrays are converted via `quantlib.math.matrix.pyx`

```cython
def to_ndarray(self):
    cdef np.npy_intp[2] dims
    dims[0] = self._thisptr.rows()
    dims[1] = self._thisptr.columns()
    cdef arr = np.PyArray_SimpleNew(2, &dims[0], np.NPY_DOUBLE)
    cdef double[:,::1] r = arr
    cdef size_t i, j
    for i in range(dims[0]):
        for j in range(dims[1]):
            r[i,j] = self._thisptr[i][j]
    return arr
```

Similarly, datetime.date's are converted via `quantlib.time.date.pyx`

```cython
def object _pydate_from_qldate(QlDate qdate):
    """ Converts a QuantLib Date (C++) to a datetime.date object. """

    cdef int m = qdate.month()
    cdef int d = qdate.dayOfMonth()
    cdef int y = qdate.year()

    return date_new(y, m, d)
```
