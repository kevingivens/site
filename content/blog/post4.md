Title: Black Variance Surface in PyQL
Date: 2020-01-04 12:20
Category: Finance
Tags: QuantLib, Volatility

Summary: Building Black Variance Surfaces in PyQL

In my previous [post](lostinthelyceum.com/Variance-Swaps-in-PyQL.html) on Variance
Swaps, I neglected to mention an important implementation detail.  If you look
the Variance Swap unittest or example script you'll see that replicating pricer
requires a ``BlackVarianceSurface`` object.  I had to build bindings for these
in PyQL so I thought I'd mention how they work.

``BlackVarianceSurface`` is a volatility termstructure that implements different
types of 2-d interpolation routines between implied volatility quotes. I included
two types of interpolations from the Quantlib source code:

* Bilinear
* Bicubic

To over simplfy, Bilinear linearly interpolates between neighboring quotes.
Bicubic uses a cubic spline routine (third order polynomial) to smoothly
interpolate between points.

See for [wikipedia](https://en.wikipedia.org/wiki/Bicubic_interpolation) for a
nice summary of the differences between bicubic vs. bilinear interpolation.

The python interface is given in the example below


```python
...
dc = Actual365Fixed()
calendar = UnitedStates()

calculation_date = Date(6, 11, 2015)

spot = 659.37
Settings.instance().evaluation_date = calculation_date

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

dates = [
    Date(6,12,2015),
    Date(6,1,2016),
    Date(6,2,2016),
    Date(6,3,2016),
]

strikes = [527.50, 560.46, 593.43, 626.40]

data = np.array(
    [
        [0.37819, 0.34177, 0.30394, 0.27832],
        [0.3445, 0.31769, 0.2933, 0.27614],
        [0.37419, 0.35372, 0.33729, 0.32492],
        [0.34912, 0.34167, 0.3355, 0.32967],
        [0.34891, 0.34154, 0.33539, 0.3297]
    ]
)

vols = Matrix.from_ndarray(data)

# Build the Black Variance Surface
black_var_surf = BlackVarianceSurface(
    calculation_date, NullCalendar(), dates, strikes, vols, dc
)

strike = 600.0
expiry = 0.2 # years

# The Surface interpolation routine can be set below (Bilinear is default)
black_var_surf.set_interpolation(Bilinear)
print("black vol bilinear: ", black_var_surf.blackVol(expiry, strike))
black_var_surf.set_interpolation(Bicubic)
print("black vol bicubic: ", black_var_surf.blackVol(expiry, strike))
```

As a sanity checked, I re-implemented results from an excellent blog
[post](http://gouthamanbalaraman.com/blog/volatility-smile-heston-model-calibration-quantlib-python.html)
by Gouthaman Balaraman.  In that post, the author builds a BlackVarianceSurface
object using Quantlib's swig bindings.

The plots for the same market data are given below:  

For Bilinear interpolation, the surface looks like

![png]({attach}post4_files/BlackVol_Bilinear.png)

For Bicubic interpolation, the surface looks like

![png]({attach}post4_files/BlackVol_Bicubic.png)

As you can see from the plots, the bicubic is slightly smoother than bilinear.

Take a look at the PyQL bindings on my [github](https://github.com/kevingivens/pyql) page to see how the
``BlackVarianceSurface`` is implemented.  The script to generate the plots is [here](https://github.com/kevingivens/Blog/tree/master/2020/BlackVol)  

One thing that I clearly need to improve is the flexibility on the volatility data
structure input to the BlackVarianceSurface constructor. It would be better to
allow the ``vols`` data structure to be either a list of lists, a numpy array,
or a QL Matrix object.  I'll try to fix that at some point.

See you next time.
