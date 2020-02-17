Title: Local Volatility in PyQL
Date: 2020-01-04 15:20
Category: Finance
Tags: QuantLib, Volatility

Summary: Local Volatility Surface in PyQL

Following on my previous [post](lostinthelyceum.com/Black-Variance-Surface-in-PyQL.html),
I wanted to review the important concept of Local Volatility.
Many [books](https://books.google.com/books/about/The_Volatility_Surface.html?id=P7ASlvLRsKMC&source=kp_book_description)
and articles [1](https://en.wikipedia.org/wiki/Local_volatility), [2](http://web.math.ku.dk/~rolf/teaching/ctff03/Gatheral.1.pdf) are dedicated
to discussing this topic.  I won't go into great detail here, I just want to give a basic overview along with implementation details in PyQL.

Essentially, the idea of Local Volatility is to identify a *level-dependent* diffusion that *exactly* reproduces market implied volatilities.  The contribution of [Dupire](https://web.archive.org/web/20120907114056/http://www.risk.net/data/risk/pdf/technical/2007/risk20_0707_technical_volatility.pdf) was to prove that
this diffusion is *unique*  while also providing a convenient technique for deriving it from market quotes.

The full derivation of the local volatility function is given in section 2.2 and the appendix of [2](http://web.math.ku.dk/~rolf/teaching/ctff03/Gatheral.1.pdf).  Here, I'll just give a sketch of the approach.

To begin, consider a generic, *level-dependent*, 1-D Brownian motion

$$
\frac{\partial S}{S} = \mu(t, S)\partial t + \sigma(t,S)\partial W
$$


Note that, the volatility for this process is **not** itself stochastic.  We can use
this process to model the diffusion on a equity spot price in the presence of
a short rate $r(t)$ and a dividend yield $D(t)$.  A European call option for this process
then satisfies a modified version of the Black-Scholes equation:

$$
\frac{\partial{C}}{\partial{t}} = \frac{\sigma^2K^2}{2}\frac{\partial^2C}{\partial K^2} + (r(t) - D(t))\left(C- K\frac{\partial{C}}{\partial{K}}\right)
$$

We can simplify this equation by writing $C(S_0, K,T)$ as a function of the forward price
$F_T=S_0\exp(\int_0^T\mu(t)dt) = S_0\exp(\int_0^T(r(t) - D(t))dt)$, (i.e. use the forward measure)

In these units, Black-Scholes equation simplifies to

$$
\frac{\partial C}{\partial t} = \frac{\sigma^2K^2}{2}\frac{\partial^2 C}{\partial K^2}
$$

or solving for the volatility gives Dupire's equation

$$
\sigma^2(K,T) =  \frac{\frac{\partial C}{\partial T}}{\frac{1}{2}K^2\frac{\partial^2 C}{\partial K^2}}
$$

Market quotes are usually given in terms of Black-Scholes implied volatilities.
We can express the local volatility in terms of these quantities by equating the
price equations for the two models

$$
C_{local}(S_0, K,T) = C_{BS}(S_0, K, \sigma_{BS}, T)
$$

The strategy is then to solve for the local volatility in terms of the Black-Scholes
impliedvolatility since we have a closed form expression for the $C_{BS}$.  The full derivation is given in section 2.2 of [2](http://web.math.ku.dk/~rolf/teaching/ctff03/Gatheral.1.pdf)
.  Here we just reproduce the results.

Namely, using more convenient units, the Black-Scholes total variance

$$
w(S_0,K,T) = \sigma^2_{BS}(S_0,K,T)T
$$

and log-moneyness
$$y = \ln\left(\frac{K}{F_T}\right)$$

We can show that the local variance
$$v_{local} = \sigma^2(S_0, K,T)$$

satisfies the following expression:
$$
v_{local} = \frac{\frac{\partial w}{\partial T}}{1 - \frac{y}{w}\frac{\partial w}{\partial y} + \frac{1}{4}\left(-\frac{1}{4} - \frac{1}{w} + \frac{y^2}{w^2}\right)\left(\frac{\partial w}{\partial y}\right)^2 + \frac{1}{2}\left(\frac{\partial^2 w}{\partial y^2}\right)}
$$

Quantlib implements this equation in ``ql.termstructure.volatility.equityfx.localvolsurface``


In the code excerpt below we, show the LocalVolSurface is used in PyQL.  It follows
a similiar interface and BlackVarianceSurface given in the previous [post](lostinthelyceum.com/Black-Variance-Surface-in-PyQL.html).  

```python
calc_date = Date(6, 11, 2015)
Settings().evaluation_date = calc_date

risk_free_rate = 0.01
dividend_rate = 0.0

day_count = Actual365Fixed()
calendar = UnitedStates()

flat_ts = FlatForward(calc_date, risk_free_rate, day_count)
dividend_ts = FlatForward(calc_date, dividend_rate, day_count)

expiration_dates = [
    Date(6,12,2015),
    Date(6,1,2016),
    Date(6,2,2016),
    Date(6,3,2016),
    Date(6,4,2016)
]

strikes = [527.50, 560.46, 593.43, 626.40]

data = np.array(
    [
        [0.37819,0.34450,0.37419,0.37498,0.35941],
        [0.34177,0.31769,0.35372,0.35847,0.34516],
        [0.30394,0.29330,0.33729,0.34475,0.33296],
        [0.27832,0.27614,0.32492,0.33399,0.32275]
    ]
)

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

In the plots below, we can see what the LocalVolSurface looks like:

![png]({attach}post5_files/LocalVol.png)

Take a look at the PyQL bindings on my [github](https://github.com/kevingivens/pyql)
to see an example of the  ``LocalVolSurface``. See you next time.
