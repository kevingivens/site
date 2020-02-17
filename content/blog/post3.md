Title: Variance Swaps in PyQL
Date: 2020-01-04 10:20
Category: Finance
Tags: QuantLib, PyQL, Pricing

Summary: We review the Variance Swap replicating pricer in QuantLib and its implementation in PyQL

### Introduction

Recently, I had the opportunity to extend the [PyQL](https://github.com/enthought/pyql) library to include variance swaps pricers.  I thought I'd take the chance to review the pricing of Variance Swaps in Quantlib (to refresh my own memory if nothing else).

As a reminder, a variance swap is a forward contract on realized variance, i.e.
it has the following payoff at maturity

$$ N(\sigma_R^2{\tau} - K) $$

Where $N$ is the notional, $\sigma_R^2{\tau}$ is the realized variance at maturity,
$\tau$, and $K$ is the strike. This instrument can be used to provide pure exposure to variance.  This is different then, for instance, a vanilla option which has variance (or volatility) exposure but also includes exposure to other risk factors such as the spot risk (delta).  

Quantlib includes two different pricing engines, ``ReplicatingVarianceSwapEngine``
and ``MCVarianceSwapEngine``.  As you might have guessed, ``ReplicatingVarianceSwapEngine``
uses a replicating portfolio to price a VarianceSwap and ``MCVarainceSwapEngine``
uses a Monte Carlo simulation. For this post, I'm going to focus on the
replicating engine as the MCEngine is conventional and not terribly interesting.

The replicating portfolio technique is described in thorough detail in [Derman](https://www.semanticscholar.org/paper/More-than-You-ever-Wanted-to-Know-about-Volatility-Demeterfi-Derman/3d9cfbe5ff32fd805f79c85b1e48fa9ac84e9128) In essence, the idea of this (or any) replicating pricer is to reproduce the payoff of the variance swap using a portfolio of liquid vanilla instruments.  
In [Derman](https://www.semanticscholar.org/paper/More-than-You-ever-Wanted-to-Know-about-Volatility-Demeterfi-Derman/3d9cfbe5ff32fd805f79c85b1e48fa9ac84e9128), the authors show that a replicating portfolio can be constructed from a weighted combination of European Calls and Puts.  We derive this
portfolio in the next section.

The derivation the the replicating portfolio is somewhat indirect.  The authors
introduce a fictitious instrument known as log contract that exactly replicates the variance swap payoff.  They then show that the log contract can itself be replicated by the particular combination of European puts and calls.  

That being said, the Quantlib implementation is pretty straight forward.
I directly adapted the variance swap unittests from Quantlib into PyQL
(``tests/test_variance_swap.py``)  You can find an example variance swap using
the ``ReplicatingVarianceSwapEngine`` in that script.

The important sections are given below

```python
# The Variance Swap is constructed
#Type, Strike, Notional, Start, End
strike = 0.04
notional = 50000
start = today()
end = start + int(0.246575*365+0.5) # This is weird value but it was in the Quantlib unittest
var_swap = VarianceSwap(SwapType.Long, 0.04, 50000, start, end)

# Option Data used in the replicating engine
replicating_option_data = [
   {'type':OptionType.Put,  'strike':50,  'v':0.30},
   {'type':OptionType.Put,  'strike':55,  'v':0.29},
   {'type':OptionType.Put,  'strike':60,  'v':0.28},
   {'type':OptionType.Put,  'strike':65,  'v':0.27},
   {'type':OptionType.Put,  'strike':70,  'v':0.26},
   {'type':OptionType.Put,  'strike':75,  'v':0.25},
   {'type':OptionType.Put,  'strike':80,  'v':0.24},
   {'type':OptionType.Put,  'strike':85,  'v':0.23},
   {'type':OptionType.Put,  'strike':90,  'v':0.22},
   {'type':OptionType.Put,  'strike':95,  'v':0.21},
   {'type':OptionType.Put,  'strike':100, 'v':0.20},
   {'type':OptionType.Call, 'strike':100, 'v':0.20},
   {'type':OptionType.Call, 'strike':105, 'v':0.19},
   {'type':OptionType.Call, 'strike':110, 'v':0.18},
   {'type':OptionType.Call, 'strike':115, 'v':0.17},
   {'type':OptionType.Call, 'strike':120, 'v':0.16},
   {'type':OptionType.Call, 'strike':125, 'v':0.15},
   {'type':OptionType.Call, 'strike':130, 'v':0.14},
   {'type':OptionType.Call, 'strike':135, 'v':0.13},
]

# The engine is constructed
engine = ReplicatingVarianceSwapEngine(process,
                                       call_strikes,
                                       put_strikes,
                                       5.0) # dK, shift below lowest put strike

# attach the engine to the swap
var_swap.set_pricing_engine(engine)

print("strike: ", var_swap.strike)
print("postion: ", var_swap.position)
print("variance: ", var_swap.variance)

```
The output is:
```
strike: 0.04
postion: SwapType.Long
variance: 0.0419
```
## Deriving the Replicating Portfolio

Briefly, from the definition of the variance strike given above, we see that the par strike of a variance swap is the expected realized variance, i.e.

$$ K_{var} = \frac{1}{T}\mathbf{E}\left[\int^T_0 \sigma^2(t, \dots)dt\right] $$

The first step in the derivation is to re-write this expression.  We consider a generic Ito process of the following form:

$$\frac{dS_t}{S_t} = \mu(t, \dots) dt + \sigma(t, \dots) dW_t $$

Where $\mu$ and $\sigma$ can be time or level dependent. Applying Ito's lemma to $\ln(S_t)$ and subtracting the above equation gives

$$\frac{dS_t}{S_t} - d\left(\ln(S_t)\right) = \frac{1}{2}\sigma^2dt$$

We insert this expression into the $K_{var}$ definition to get

$$
\begin{align}
K_{var} =& \frac{2}{T}\mathbf{E}\left[\int^T_0 \frac{\partial S_t}{S_t} - \ln\left(\frac{S_T}{S_0}\right)\right] \\
\end{align}
$$

Next, we partition the strike domain by introducing a cutoff strike value, $S_* \in (0, \infty)$.  In what follows this cutoff will be set to lower bound of put strikes, but for now we leave it arbitrary.

The allows us the write $K_{var}$ as

$$
\begin{align}
K_{var} =& \frac{2}{T}\mathbf{E}\left[\int^T_0 \frac{\partial S_t}{S_t} - \frac{S_T- S_*}{S_*}- \ln\left(\frac{S_*}{S_0}\right) + \frac{S_T- S_*}{S_*} -\ln\left(\frac{S_T}{S_*}\right)\right]
\end{align}
$$

We can then use the fact that in the risk neutral measure

$$
\mathbf{E}\left[\int^T_0 \frac{\partial S_t}{S_t}dt\right] = rT
$$

(i.e. martingales are driftless) Distributing the expectation value gives

$$
K_{var} = \frac{2}{T}\left[rT - \left(\frac{S_0}{S_*}e^{rT} - 1\right) - \ln\left(\frac{S_*}{S_0}\right)\right] + e^{rT}\frac{2}{T}\mathbf{E}\left[ \frac{S_T- S_*}{S_*} -\ln\left(\frac{S_T}{S_*}\right)\right]
$$


This expression implies that the variance swap can be replicated by an option with the following payoff

$$
f(S_T) = \frac{2}{T}\left(\frac{S_T-S_*}{S_*} - \ln\frac{S_T}{S_*}\right) \label{eq1}
$$

This option is the so-called *log-contract*, which obviously only exists in the minds of quants.

The final trick to recognize that the log-contract can itself be replicated as linear combination of European calls and puts (which thankfully do exist!).  We first consider the strike, $K$, as a *continuous* variable.  We then can build a portfolio that matches the log contract's payoff by weighting the options with the inverse of their strikes.

Namely, we can show that
$$
 \frac{S_T- S_*}{S_*} -\ln\left(\frac{S_T}{S_*}\right) = \int^{S_*}_0 dK\frac{\max[K- S(T),0]}{K^2} + \int_{S_*}^{\infty} dK\frac{\max[S(T)- K, 0]}{K^2}
$$


So we can approximate the price of the log-contract by expanding the expectation value
as a sum of European calls and puts

$$
\begin{align}
\mathbf{E}\left[ \frac{S_T- S_*}{S_*} -\ln\left(\frac{S_T}{S_*}\right)\right] &=
\mathbf{E}\left[ \int^{S_*}_0 dK\frac{\max[K- S(T),0]}{K^2} + \int_{S_*}^{\infty} dK\frac{\max[S(T)- K, 0]}{K^2} \right] \\
 & =\int^{S_*}_0 \frac{dK}{K^2} \mathbf{E}\left[\max[K- S(T),0]\right] + \int_{S_*}^{\infty} \frac{dK}{K^2}\mathbf{E}\left[\max[S(T)- K, 0]\right] \\
  & =\int^{S_*}_0 \frac{dK}{K^2} P(K,T) + \int_{S_*}^{\infty} \frac{dK}{K^2}C(K,T) \\
\end{align}
$$
$S_*$ is then set to the put strike lower bound, $S_*  = K_{Put_1} - dK$.  In the numerical example given above $S_*  = 50 - 5 = 45$.

Take a look at the PyQL bindings on my [github](https://github.com/kevingivens/pyql) page to see how the
``ReplicatingVarianceSwapEngine`` is implemented.

See you next time.
