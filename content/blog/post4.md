Title: Black Variance Surface in PyQL
Date: 2020-01-04 10:20
Category: Finance
Tags: Numerical Methods

Summary: Devito allows users to build finite difference schemes in python and "compile-down" to optimized C++


## Introduction

In my previous [post]() on Variance Swaps, I neglected to mention an
important implementation detail.  If you look the Variance Swap unittests you'll
see that replicating pricer example requires a ``BlackVarianceSurface`` object.  
I had to build bindings for these in PyQL so I thought I'd mention how they work.

``BlackVarianceSurface`` is a volatility termstructure that implements different
types of interpolation routines between implied volatility quotes.  
I included two types of interpolations from the Quantlib source code:

* Bilinear
* Bicubic

Essentially, Bilinear linearly interpolates between neighboring quotes.
Bicubic uses a cubic spline routine to smoothly interpolates between points.

See for [wikipedia](https://en.wikipedia.org/wiki/Bicubic_interpolation) for a
nice summary of bicubic vs. bilinear interpolation.

As a sanity checked, I re-implemented results from an excellent blog [post]() by Goutham.  
In that post, the author builds a BlackVarianceSurface object using Quantlib's swig bindings.

The plots for the same market data are given below:       


```python
calculation_date = Date(6, 11, 2015)

spot = 659.37
Settings.instance().evaluationDate = calculation_date

dividend_yield = SimpleQuote(0.0)
risk_free_rate = 0.01
dividend_rate = 0.0
# bootstrap the yield/dividend/vol curves
flat_term_structure = FlatForward(
    reference_date=calculation_date,
    forward=risk_free_rate,
    daycounter=dc
)

flat_dividend_ts = FlatForward(
    reference_date=calculation_date,
    forward=dividend_yield,
    daycounter=dc
)

expiration_dates = [Date(6,12,2015), Date(6,1,2016), Date(6,2,2016),
                    Date(6,3,2016), Date(6,4,2016), Date(6,5,2016),
                    Date(6,6,2016), Date(6,7,2016), Date(6,8,2016),
                    Date(6,9,2016), Date(6,10,2016), Date(6,11,2016),
                    Date(6,12,2016), Date(6,1,2017), Date(6,2,2017),
                    Date(6,3,2017), Date(6,4,2017), Date(6,5,2017),
                    Date(6,6,2017), Date(6,7,2017), Date(6,8,2017),
                    Date(6,9,2017), Date(6,10,2017), Date(6,11,2017)]

strikes = [527.50, 560.46, 593.43, 626.40, 659.37, 692.34, 725.31, 758.28]

data = np.array([
[0.37819, 0.34177, 0.30394, 0.27832, 0.26453, 0.25916, 0.25941, 0.26127],
[0.3445, 0.31769, 0.2933, 0.27614, 0.26575, 0.25729, 0.25228, 0.25202],
[0.37419, 0.35372, 0.33729, 0.32492, 0.31601, 0.30883, 0.30036, 0.29568],
[0.37498, 0.35847, 0.34475, 0.33399, 0.32715, 0.31943, 0.31098, 0.30506],
[0.35941, 0.34516, 0.33296, 0.32275, 0.31867, 0.30969, 0.30239, 0.29631],
[0.35521, 0.34242, 0.33154, 0.3219, 0.31948, 0.31096, 0.30424, 0.2984],
[0.35442, 0.34267, 0.33288, 0.32374, 0.32245, 0.31474, 0.30838, 0.30283],
[0.35384, 0.34286, 0.33386, 0.32507, 0.3246, 0.31745, 0.31135, 0.306],
[0.35338, 0.343, 0.33464, 0.32614, 0.3263, 0.31961, 0.31371, 0.30852],
[0.35301, 0.34312, 0.33526, 0.32698, 0.32766, 0.32132, 0.31558, 0.31052],
[0.35272, 0.34322, 0.33574, 0.32765, 0.32873, 0.32267, 0.31705, 0.31209],
[0.35246, 0.3433, 0.33617, 0.32822, 0.32965, 0.32383, 0.31831, 0.31344],
[0.35226, 0.34336, 0.33651, 0.32869, 0.3304, 0.32477, 0.31934, 0.31453],
[0.35207, 0.34342, 0.33681, 0.32911, 0.33106, 0.32561, 0.32025, 0.3155],
[0.35171, 0.34327, 0.33679, 0.32931, 0.3319, 0.32665, 0.32139, 0.31675],
[0.35128, 0.343, 0.33658, 0.32937, 0.33276, 0.32769, 0.32255, 0.31802],
[0.35086, 0.34274, 0.33637, 0.32943, 0.3336, 0.32872, 0.32368, 0.31927],
[0.35049, 0.34252, 0.33618, 0.32948, 0.33432, 0.32959, 0.32465, 0.32034],
[0.35016, 0.34231, 0.33602, 0.32953, 0.33498, 0.3304, 0.32554, 0.32132],
[0.34986, 0.34213, 0.33587, 0.32957, 0.33556, 0.3311, 0.32631, 0.32217],
[0.34959, 0.34196, 0.33573, 0.32961, 0.3361, 0.33176, 0.32704, 0.32296],
[0.34934, 0.34181, 0.33561, 0.32964, 0.33658, 0.33235, 0.32769, 0.32368],
[0.34912, 0.34167, 0.3355, 0.32967, 0.33701, 0.33288, 0.32827, 0.32432],
[0.34891, 0.34154, 0.33539, 0.3297, 0.33742, 0.33337, 0.32881, 0.32492]])

```
For Bilinear interpolation, the surface looks like

For Bicubic interpolation, the surface looks like


Take a look at the PyQL bindings on my [github] page to see how the
``BlackVarianceSurface`` is implemented.  

One thing that I clearly need to improve is the flexibility on the volatility data
structure input to the BlackVarianceSurface constructor. It would be better to
allow the ``vols`` data structure to be either a list of lists, a numpy array,
or a QL Matrix object.  I'll try to fix that at some point.

See you next time.