"""Predict the future account balance from past monthly transaction history."""

import math

import numpy as np
import pandas as pd

from financial_analysis_tool.transaction_history import TransactionHistory


def next_months(last_month: str, count: int) -> list:
    """Return the next 'count' months after last_month."""
    year = int(last_month[:4])
    month = int(last_month[5:])
    months = []
    for _ in range(count):
        month += 1
        if month > 12:
            month = 1
            year += 1
        months.append(f"{year}-{month:02d}")
    return months


class BalanceForecast:
    """Predict the balance by adding the typical monthly net each month.

    The typical monthly net is either the median of the last 'recent_months'
    (default) or the mean of the last 'recent_months'.
    Therefore, the forecast assumes a typical future without large sudden income
    or expenses.
    """

    def __init__(
        self,
        history: TransactionHistory,
        starting_balance: float = 0.0,
        method: str = "median",
        recent_months: int = 12,
    ):
        if method not in ("median", "mean"):
            raise ValueError(f"method must be 'median' or 'mean', not {method!r}")
        self.history = history
        self.starting_balance = starting_balance
        self.method = method
        self.recent_months = recent_months

    def __repr__(self):
        return (
            f"BalanceForecast(start={self.starting_balance:.2f}, "
            f"{self.method} monthly net={self.monthly_net:.2f})"
        )

    @property
    def monthly_net(self) -> float:
        """Return the typical net change in balance per month,

        This typical net change depends on the specified method.
        """
        net = self.history.last_months(self.recent_months).monthly_summary()["Net"]
        if self.method == "median":
            return net.median()
        return net.mean()

    def predict(self, months: int = 12) -> pd.DataFrame:
        """Return the predicted balance at the end of each of the next 'months'."""
        if months < 1:
            raise ValueError("months must be at least 1")
        steps = np.arange(1, months + 1)
        balances = self.starting_balance + self.monthly_net * steps
        labels = next_months(self.history.months[-1], months)
        # Returns DataFrame with future months with their respective
        # forecasted balance.
        return pd.DataFrame({"Month": labels, "Balance": balances})

    def balance_in(self, months: int) -> float:
        """Return the predicted balance after the given number of months."""
        return self.predict(months)["Balance"].iloc[-1]

    def months_until(self, target: float) -> int | None:
        """Return how many months the user needs to reach a specific target balance.

        It returns 0 if the target is already reached, and None if it will
        never be reached because the balance is not growing.
        """
        if self.starting_balance >= target:
            return 0
        if self.monthly_net <= 0:
            return None
        return math.ceil((target - self.starting_balance) / self.monthly_net)