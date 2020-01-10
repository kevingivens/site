Title: Variance Swaps in PyQL
Date: 2020-01-04 10:20
Category: Finance
Tags: QuantLib, PyQL, Pricing

Summary: We review the Variance Swap pricer in QuantLib and their implemenation in PyQL

### Introduction

Recently, I had the opportunity to extend the [PyQL](https://github.com/enthought/pyql) library to include variance swaps pricers.  I thought I'd take the chance to review the pricing of Variance Swaps in Quantlib (to refresh my own memory if nothing else).

As a reminder, a variance swap is a forward contract on realized variance, i.e.
it has the following payoff at maturity

$$ N(\sigma_R^2{\tau} - K) $$

Where $N$ is the notional, $\sigma_R^2{\tau}$ is the realized variance at maturity,
$\tau$, and $K$ is the strike. This instrument can be used to provide pure exposure to variance.  This is different then, for instance, a vanilla option which has variance (or volatility) exposure but also includes exposure to other risk factors such as the spot risk (delta).  

Quantlib includes two different pricing engines, ``ReplicatingVarianceSwapEngine``
and ``MCVarianceSwapEngine``.  As you might have guessed, ``ReplicatingVarianceSwapEngine``
use a replicating portfolio to price a VarianceSwap and ``MCVarainceSwapEngine``
uses a Monte Carlo simulation. For this post I'm going to focus on the
replicating engine as the MCEngine is conventional, and therefore not terribly interesting.

The replicating portfolio technique is described in thorough detail in [Derman](https://www.semanticscholar.org/paper/More-than-You-ever-Wanted-to-Know-about-Volatility-Demeterfi-Derman/3d9cfbe5ff32fd805f79c85b1e48fa9ac84e9128)
In essence, the idea of this (or any) replicating pricer is to reproduce the
payoff of the variance swap using a portfolio of liquid vanilla instruments.  
In [Derman](https://www.semanticscholar.org/paper/More-than-You-ever-Wanted-to-Know-about-Volatility-Demeterfi-Derman/3d9cfbe5ff32fd805f79c85b1e48fa9ac84e9128), the authors show that a replicating portfolio can be constructed from
a weighted combination of European Calls and Puts.  We derive this
portfolio in the next section.

The derivation the the replicating portfolio is somewhat indirect.  The authors
first introduce a fictitious instrument known as log contract that
exactly replicates the variance swap payoff.  They then show that the log
contract can itself be replicated by the particular combination of puts and calls.  

One could argue that a more direct approach would be to simply show that the variance swap can be approximately replicated using calls and puts.  I'm guessing the log contract might be used to guide intuition.  I honestly don't know.

That being said, the Quantlib implementation is pretty straight forward.
I directly adapted the variance swap unittests from Quantlib into pyQL
(``tests/test_variance_swap.py``)  You can find an example variance swap using
the ``ReplicatingVarianceSwapEngine`` in that script.

The important sections are given below

```python
# The Variance Swap is constructed
#Type, Strike, Notional, Start, End
strike = 0.04
notional = 50000
start = today()
end = start + int(0.246575*365+0.5) # This is weird but it was in Quantlib
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

# The engine is constructed and attached to the swap
engine = ReplicatingVarianceSwapEngine(process,
                                       call_strikes,
                                       put_strikes,
                                       5.0) # dK, shift below lowest put strike

# The swap is priced
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

Briefly, the par strike for a variance swap is the expected realized variance, i.e.

$$ K_{var} = \frac{1}{T}\mathbf{E}\left[\int^T_0 \sigma^2(t, \dots)dt\right] $$

The first step in the derivation is to re-write this expression.  For a Black Scholes-like spot process

$$\frac{dS_t}{S_t} = \mu(t, \dots) dt + \sigma(t, \dots) dW_t $$

Applying Ito's lemma to $\ln(S_t)$ and subtracting the above equation gives

$$\frac{dS_t}{S_t} - d(\ln(S_t)) = \frac{1}{2}\sigma^2dt$$

We insert this expression into the $K_{var}$ to get

<!--$$ K_{var} = \frac{2}{T}\left[rT - \left(\frac{S_T}{S_*}\exp^{rT} -1) -\log\frac{S_*}{S_0} \right) \right]$$-->

$$
\begin{align}
K_{var} =& \frac{2}{T}\mathbf{E}\left[\int^T_0 \frac{\partial S_t}{S_t} - \ln\left(\frac{S_T}{S_0}\right)\right] \\
        =& \frac{2}{T}\mathbf{E}\left[\int^T_0 \frac{\partial S_t}{S_t} - \frac{S_T- S_*}{S_*}- \ln\left(\frac{S_*}{S_0}\right) + \frac{S_T- S_*}{S_*} -\ln\left(\frac{S_T}{S_*}\right)\right]
\end{align}
$$

Where we introduce $S_*$ as the Put strike range lower bound, i.e. $S_*  = K_{Put_1} - dK$. From the example given above $S_*  = 50 - 5 = 45$.  

Distributing the expectation value gives

$$K_{var} = \frac{2}{T}\left[rT - \left(\frac{S_0}{S_*}e^{rT} - 1\right) - \ln\left(\frac{S_*}{S_0}\right)\right] + e^{rT}\frac{2}{T}\mathbf{E}\left[ \frac{S_T- S_*}{S_*} -\ln\left(\frac{S_T}{S_*}\right)\right]$$

Where we have used the fact that, in the risk neutral measure
$$\mathbf{E}\left[\int^T_0 \frac{\partial S_t}{S_t}dt\right] = rT$$

This expression implies that the par variance strike can be replicated with an option with the following payoff

$$ f(S_T) = \frac{2}{T}\left(\frac{S_T-S_*}{S_*} - \ln\frac{S_T}{S_*}\right) $$

It's this option that is approximated with a combination of puts and calls.  
Namely, The continuous payoff function given above is is approximated by a series of
put and call payoff functions that represent the instantaneous slope of the payoff function.

In the plot below I demonstrate the idea

$$ \Pi = \sum_i w_iP(S,K_i) + \sum_j w_jC(S,K_j)$$
The weights in the portfolio are then the instance slope of the payoff function  

```python
import numpy as np
import matplotlib.plot at plt

K = np.array(50,135, 5)
K_D = np.array(50,135,1)
F = f

def f(S, T, S0 = 45):
    return (2/T)*((S-S0)/S0 - np.log(S/S0))

def weight(K1, K2):
   return (f(S, T, S0) - f(S, T, S0))/(K2 - K1)


call_weights = [0]
for call, i in enumerate(calls[1:]):
    call_weights.append(weight(call['K'], calls[i-1]['K']) - call_weights[:i-1].sum())

```



$$ \Vega_{var} = \frac{\partial C}{\partial \sigma^2} = \frac{S\sqrt{\tau}}{2\sqrt{2\pi}\sigma}\exp\left(\frac{-d_1^2}{2}\right) $$

where $d1$ is the conventional Black Scholes CDF argument $d_1 = \frac{\ln(\frac{S}{K}) + (r - \frac{\sigma^2}{2})\tau}{\sigma\sqrt{\tau}}$

As a fun exercise can now show that the variance swap does in fact of zero spot exposure
Show Vega, Variance Sensies Plot

```python

def variance_vega(S,t,sigma,K,r):
    d_1 = (np.log(S/K) + (r - (sigma**2/2))*t)/(sigma*np.sqrt(t))
    return (S*np.sqrt(t))/(2*np.sqrt(2*np.pi)*sigma)*np.exp(-d_1**2/2)


payoff NB not Call/Put ...

```
