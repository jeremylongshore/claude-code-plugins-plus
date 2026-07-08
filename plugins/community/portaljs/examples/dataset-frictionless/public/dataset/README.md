CBOE Volatility Index (VIX) time-series dataset including daily open, close,
high and low. The CBOE Volatility Index (VIX) is a key measure of market
expectations of near-term volatility conveyed by S&P 500 stock index option
prices introduced in 1993.

## Data

From the [VIX FAQ][faq]:

> In 1993, the Chicago Board Options Exchange® (CBOE®) introduced the CBOE
> Volatility Index®, VIX®, and it quickly became the benchmark for stock market
> volatility. It is widely followed and has been cited in hundreds of news
> articles in the Wall Street Journal, Barron's and other leading financial
> publications. Since volatility often signifies financial turmoil, VIX is
> often referred to as the "investor fear gauge".
>
> VIX measures market expectation of near term volatility conveyed by stock
> index option prices. The original VIX was constructed using the implied
> volatilities of eight different OEX option series so that, at any given time,
> it represented the implied volatility of a hypothetical at-the-money OEX
> option with exactly 30 days to expiration.
>
> The New VIX still measures the market's expectation of 30-day volatility, but
> in a way that conforms to the latest thinking and research among industry
> practitioners. The New VIX is based on S&P 500 index option prices and
> incorporates information from the volatility "skew" by using a wider range of
> strike prices rather than just at-the-money series.

[faq]: http://www.cboe.com/micro/vix/faq.aspx

## Preparation

You will need Python 3.6 or greater and dataflows library to run the script

To update the data run the process script locally:

```
# Install dataflows
pip install dataflows

# Run the script
python flows/finance-vix.py
```

### TODO

* Incorporate computed historical data (1990-2003)
* Consider incorporating VOX data

## License

No obvious statement on [historical data page][historical]. Given size and
factual nature of the data and its source from a US company would imagine this
was public domain and as such have licensed the Data Package under the Public
Domain Dedication and License (PDDL).

[historical]: http://www.cboe.com/micro/vix/historical.aspx
