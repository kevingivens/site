Title: Local Volatility in PyQL
Date: 2020-01-04 10:20
Category: Finance
Tags: Numerical Methods

Summary: Devito allows users to build finite difference schemes in python and "compile-down" to optimized C++

## Introduction

Following on my previous post[], I wanted to review an important concept in
volatility modeling. In particular, I wanted to discuss local volatility and how
it's implemented in Quantlib.

Many books[] and lectures[] are dedicated to discussing this topic.  I won't be
able to discuss it in great detail in a blog post I just want to give a basic
overview along with implementation details in pyQL.

Essentially, the idea of Local Volatility is to first consider a diffusion of
the following form

$$\partial S = \mu(t, S)\partial t + \sigma(t,S)\partial W$$  

In particular, the volatility, $\sigma$, is a function of time, $t$, and level, $S$,
but is not itself a random process as it would be in a stochastic volatility
model. The question, first addressed by Dupire[], was whether such a model could
be made to fit an arbitrary set of implied volatility quotes.  In his original
paper Dupire, gave a prescription for the construction of such a surface
$\sigma(t,S)$, known a local volatility.  The defining formula for this surface is

$$$$

Quantlib implements this equation in ``ql.termstructure.volatility.equityfx.localvolsurface``


important implementation detail.  If you look the Variance Swap unittests you'll
see that replicating pricer example requires a ``BlackVarianceSurface`` object.  
I had to build bindings for these in pyql so I thought I'd mention how they work.

``BlackVarianceSurface`` is a volatility termstructure that implements different
types of interpolation routines between implied volatility quotes.  
I included two types of interpolations from the Quantlib source code:

* Bilinear
* Bicubic

Essentially, Bilinear linearly interpolates between neighboring quotes.
Bicubic uses a cubic spline routine to smoothly interpolates between points.

see plot for wikipedia

As a sanity checked, I re-implemented results from an excellent blog post[] by Goutham.  
In that post, he builds a BlackVarianceSurface object using Quantlib's swig bindings.       


```python
calc_date = Date(6, 11, 2015)
Settings().evaluation_date = calc_date

risk_free_rate = 0.01
dividend_rate = 0.0

day_count = Actual365Fixed()
calendar = UnitedStates()

flat_ts = FlatForward(calc_date, risk_free_rate, day_count)
dividend_ts = FlatForward(calc_date, dividend_rate, day_count)

expiration_dates = [Date(6,12,2015),
                    Date(6,1,2016),
                    Date(6,2,2016),
                    Date(6,3,2016),
                    Date(6,4,2016)]

strikes = [527.50, 560.46, 593.43, 626.40]

data = np.array([[0.37819,0.34450,0.37419,0.37498,0.35941],
                 [0.34177,0.31769,0.35372,0.35847,0.34516],
                 [0.30394,0.29330,0.33729,0.34475,0.33296],
                 [0.27832,0.27614,0.32492,0.33399,0.32275]])

vols = Matrix.from_ndarray(data)

black_var_surf = BlackVarianceSurface(calc_date,
                                      calendar,
                                      expiration_dates,
                                      strikes,
                                      vols,
                                      day_count)

spot = 659.37
strike = 600.0
expiry = 0.2 # years

local_vol_surf = LocalVolSurface(black_var_surf,
                                 flat_ts,
                                 dividend_ts,
                                 spot)

print("local vol: ", local_vol_surf.localVol(expiry, strike))

```

In the plots below, we can see what the BlackVarianceSurface looks like for
different interpolation methods

Take a look at the pyql bindings on my github to see how the ``BlackVarianceSurface`` is implemented.  
See you next time.
