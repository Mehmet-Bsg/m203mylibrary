import math
from typing import Callable, Dict
from typing import List, Tuple, Optional
from scipy.stats import norm


class Option:
    """
    A class to represent an option and perform various option pricing and Greek calculations
    using the Black-Scholes model.
    """
    DAYS_IN_YEAR = 365

    def __init__(self, option_type: str, underlying_price: float, strike_price: float, interest_rate: float,
                 dividend_yield: float, time_to_maturity: int, implied_volatility: float):
        """
        Initializes the Option.

        :param option_type: Type of the option 'Call' or 'Put'.
        :param underlying_price: Current price of the underlying asset.
        :param strike_price: Strike price of the option.
        :param interest_rate: Risk-free interest rate.
        :param dividend_yield: Continuous dividend yield of the underlying asset.
        :param time_to_maturity: Time to maturity in days.
        :param implied_volatility: Implied volatility of the underlying asset.
        """
        if option_type not in ["Call", "Put"]:
            raise ValueError("option_type must be 'Call' or 'Put'")
        if underlying_price <= 0 or strike_price <= 0 or time_to_maturity <= 0 or implied_volatility <= 0:
            raise ValueError(
                "Underlying Price, strike price, implied volatility and time to maturity must be positive values")

        self.option_type = option_type
        self.underlying_price = underlying_price
        self.strike_price = strike_price
        self.interest_rate = interest_rate
        self.dividend_yield = dividend_yield
        self.time_to_maturity = time_to_maturity
        self.implied_volatility = implied_volatility

    @staticmethod
    def norm_dist(d: float) -> float:
        """
        Standard normal cumulative distribution function.

        :param d: Input value.
        :return: Cumulative probability.
        """
        return norm.cdf(d)

    @staticmethod
    def normal_pdf(d: float) -> float:
        """
        Standard normal probability density function.

        :param d: Input value.
        :return: Density value.
        """
        return math.exp(-d ** 2 / 2) / math.sqrt(2 * math.pi)

    def _calculate_d1_d2(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> Tuple[float, float]:
        """
        Calculates d1 and d2 for the Black-Scholes formula.

        :param S: Current price of the underlying asset.
        :param K: Strike price of the option.
        :param T: Time to maturity in years.
        :param r: Risk-free interest rate.
        :param q: Continuous dividend yield of the underlying asset.
        :param sigma: Implied volatility of the underlying asset.
        :return: Tuple containing d1 and d2.
        """
        D1 = (
                (math.log(S * math.exp(-q * T) / (K * math.exp(-r * T))) +
                 0.5 * sigma ** 2 * T) /
                (sigma * math.sqrt(T))
        )
        D2 = D1 - sigma * math.sqrt(T)
        return D1, D2

    def black_scholes(self, underlying_price: Optional[float] = None, time_to_maturity: Optional[int] = None,
                      implied_volatility: Optional[float] = None) -> float:
        """
        Calculates the Black-Scholes price of an option.

        :param underlying_price: Current price of the underlying asset. Defaults to the initialized price.
        :param time_to_maturity: Time to maturity in days. Defaults to the initialized value.
        :param implied_volatility: Implied volatility of the underlying asset. Defaults to the initialized value.
        :return: Black-Scholes price of the option.
        """
        T = self.time_to_maturity / self.DAYS_IN_YEAR if time_to_maturity is None else time_to_maturity / self.DAYS_IN_YEAR
        S = self.underlying_price if underlying_price is None else underlying_price
        K = self.strike_price
        r = self.interest_rate
        q = self.dividend_yield
        sigma = self.implied_volatility if implied_volatility is None else implied_volatility

        D1, D2 = self._calculate_d1_d2(S, K, T, r, q, sigma)

        if self.option_type == "Call":
            return (S * math.exp(-q * T) * self.norm_dist(D1) -
                    K * math.exp(-r * T) * self.norm_dist(D2))
        else:
            return (K * math.exp(-r * T) * self.norm_dist(-D2) -
                    S * math.exp(-q * T) * self.norm_dist(-D1))

    # Greek Calculations
    def delta(self, underlying_price: Optional[float] = None, time_to_maturity: Optional[int] = None,
              implied_volatility: Optional[float] = None) -> float:
        """
        Calculates the Delta of an option.

        :param underlying_price: Current price of the underlying asset. Defaults to the initialized price.
        :param time_to_maturity: Time to maturity in days. Defaults to the initialized value.
        :param implied_volatility: Implied volatility of the underlying asset. Defaults to the initialized value.
        :return: Delta of the option.
        """
        T = self.time_to_maturity / self.DAYS_IN_YEAR if time_to_maturity is None else time_to_maturity / self.DAYS_IN_YEAR
        S = self.underlying_price if underlying_price is None else underlying_price
        K = self.strike_price
        r = self.interest_rate
        q = self.dividend_yield
        sigma = self.implied_volatility if implied_volatility is None else implied_volatility

        D1, _ = self._calculate_d1_d2(S, K, T, r, q, sigma)

        if self.option_type == "Call":
            return math.exp(-q * T) * self.norm_dist(D1)
        else:
            return math.exp(-q * T) * (self.norm_dist(D1) - 1)

    def vega(self, underlying_price: Optional[float] = None, time_to_maturity: Optional[int] = None,
             implied_volatility: Optional[float] = None) -> float:
        """
        Calculates the Vega of an option.
        Change in Option Price for a +1% increase in implied volatility.

        :param underlying_price: Current price of the underlying asset. Defaults to the initialized price.
        :param time_to_maturity: Time to maturity in days. Defaults to the initialized value.
        :param implied_volatility: Implied volatility of the underlying asset. Defaults to the initialized value.
        :return: Vega of the option.
        """
        T = self.time_to_maturity / self.DAYS_IN_YEAR if time_to_maturity is None else time_to_maturity / self.DAYS_IN_YEAR
        S = self.underlying_price if underlying_price is None else underlying_price
        K = self.strike_price
        r = self.interest_rate
        q = self.dividend_yield
        sigma = self.implied_volatility if implied_volatility is None else implied_volatility

        D1, _ = self._calculate_d1_d2(S, K, T, r, q, sigma)

        return (S * math.exp(-q * T) * self.normal_pdf(D1) * math.sqrt(T) * 0.01)

    def gamma(self, underlying_price: Optional[float] = None, time_to_maturity: Optional[int] = None,
              implied_volatility: Optional[float] = None) -> float:
        """
        Calculates the Gamma of an option.
        Variation of Option Price for ΔS=1

        :param underlying_price: Current price of the underlying asset. Defaults to the initialized price.
        :param time_to_maturity: Time to maturity in days. Defaults to the initialized value.
        :param implied_volatility: Implied volatility of the underlying asset. Defaults to the initialized value.
        :return: Gamma of the option.
        """
        T = self.time_to_maturity / self.DAYS_IN_YEAR if time_to_maturity is None else time_to_maturity / self.DAYS_IN_YEAR
        S = self.underlying_price if underlying_price is None else underlying_price
        K = self.strike_price
        r = self.interest_rate
        q = self.dividend_yield
        sigma = self.implied_volatility if implied_volatility is None else implied_volatility

        D1, _ = self._calculate_d1_d2(S, K, T, r, q, sigma)

        return (self.normal_pdf(D1) * math.exp(-q * T) / (S * sigma * math.sqrt(T)))

    def theta(self, underlying_price: Optional[float] = None, time_to_maturity: Optional[int] = None,
              implied_volatility: Optional[float] = None) -> float:
        """
        Calculates the Theta of an option.
        Change in Option Price due to the passage of 1 calendar day.

        :param underlying_price: Current price of the underlying asset. Defaults to the initialized price.
        :param time_to_maturity: Time to maturity in days. Defaults to the initialized value.
        :param implied_volatility: Implied volatility of the underlying asset. Defaults to the initialized value.
        :return: Theta of the option.
        """
        T = self.time_to_maturity / self.DAYS_IN_YEAR if time_to_maturity is None else time_to_maturity / self.DAYS_IN_YEAR
        S = self.underlying_price if underlying_price is None else underlying_price
        K = self.strike_price
        r = self.interest_rate
        q = self.dividend_yield
        sigma = self.implied_volatility if implied_volatility is None else implied_volatility

        D1, D2 = self._calculate_d1_d2(S, K, T, r, q, sigma)

        if self.option_type == "Call":
            return (-S * self.normal_pdf(D1) * sigma * math.exp(-q * T) / (2 * math.sqrt(T)) +
                    q * S * self.norm_dist(D1) * math.exp(-q * T) -
                    r * K * math.exp(-r * T) * self.norm_dist(D2)) / self.DAYS_IN_YEAR
        else:
            return (-S * self.normal_pdf(D1) * sigma * math.exp(-q * T) / (2 * math.sqrt(T)) -
                    q * S * self.norm_dist(-D1) * math.exp(-q * T) +
                    r * K * math.exp(-r * T) * self.norm_dist(-D2)) / self.DAYS_IN_YEAR