"""Give text recommendations based on the transaction history.

Every recommendation is a rule: a subclass of AdviceRule with a check method
that returns a message, or None if the rule has nothing to recommend. The rules are
dependent on the most recent months, so the advice describes the current situation.

The expenses are split into three non-overlapping groups: recurring
payments (bills and subscriptions), one-off expenses (single payments larger
than a typical month's spending) and everyday spending (everything else).
Each group gets the advice that fits it.
"""

import math
from abc import ABC, abstractmethod

from financial_analysis_tool.recurring_payments import (
    find_recurring_payments,
    total_monthly_cost,
)
from financial_analysis_tool.transaction_history import TransactionHistory


def split_expenses(history: TransactionHistory) -> tuple:
    """Split the expenses into recurring, one-off and everyday spending.

    Return three DataFrames: the recurring payments, the single
    expenses larger than a typical month's spending (one-off expenses),
    and all other everyday expenses.
    """
    typical_spending = history.monthly_statistics().loc["Spending", "Median"]
    recurring_names = []
    for p in find_recurring_payments(history):
        recurring_names.append(p.description)
    expenses = history.expenses
    is_recurring = expenses["Description"].isin(recurring_names)
    is_one_off = (-expenses["Signed Amount"] > typical_spending) & ~is_recurring
    return (
        expenses[is_recurring],
        expenses[is_one_off],
        expenses[~is_recurring & ~is_one_off],
    )


class AdviceRule(ABC):
    """The abstract base class for all recommendation rules."""

    @abstractmethod
    def check(self, history: TransactionHistory) -> str | None:
        """Return a recommendation, or None if there is nothing to recommend."""


class SavingsRateRule(AdviceRule):
    """Compare the share of income that is saved with a target.

    Default target_share is 20%.
    """

    def __init__(self, target_share: float = 0.20):
        self.target_share = target_share

    def check(self, history):
        period = f"In the last {len(history.months)} months"
        if history.total_income == 0:
            return (
                f"{period}, no income was recorded, so a savings rate cannot be "
                "calculated. Check that your file includes your income."
            )
        rate = history.net / history.total_income
        if rate >= self.target_share:
            return (
                f"{period}, you saved {rate:.1%} of your income, which meets "
                f"the {self.target_share:.0%} target share, great job!"
            )
        total_extra_missing = self.target_share * history.total_income - history.net
        extra_per_month = total_extra_missing / len(history.months)
        if history.net < 0:
            deficit_per_month = -history.net / len(history.months)
            return (
                f"{period}, you spent more than you earned, on average "
                f"{deficit_per_month:,.2f} per month. To save "
                f"{self.target_share:.0%} of your income, you would need "
                f"{extra_per_month:,.2f} more per month."
            )
        return (
            f"{period}, you saved only {rate:.1%} of your income. To reach "
            f"{self.target_share:.0%}, save {extra_per_month:,.2f} more per month, "
            "by lowering your everyday spending or cancelling unwanted subscriptions."
        )


class RecurringPaymentsRule(AdviceRule):
    """Warn if recurring payments constitute the majority of normal spending.

    Set the default limit to be 60%.
    """

    def __init__(self, limit: float = 0.60):
        self.limit = limit

    def check(self, history):
        payments = find_recurring_payments(history)
        typical_spending = history.monthly_statistics().loc["Spending", "Median"]
        if not payments or typical_spending == 0:
            return None
        share = total_monthly_cost(payments) / typical_spending
        if share <= self.limit:
            return (
                f"Recurring payments make up {share:.0%} of a typical month's "
                f"spending, which is within the {self.limit:.0%} limit."
            )
        biggest = ", ".join(p.description for p in payments[:5])
        return (
            f"Recurring payments make up {share:.0%} of a typical month's "
            f"spending, mainly {biggest}. Lowering these, for example "
            "by switching to a cheaper provider or renegotiating the contract, "
            "will greatly support your budget."
        )


class EverydaySpendingRule(AdviceRule):
    """Show how much reducing everyday spending would save.

    Everyday spending is everything that is neither a recurring payment nor a
    one-off expense.
    """

    def __init__(self, spending_cut_share: float = 0.10, n: int = 5):
        self.spending_cut_share = spending_cut_share
        self.n = n

    def check(self, history):
        everyday = split_expenses(history)[2]
        if everyday.empty:
            return None
        months = len(history.months)
        # Average everyday expenses per month.
        per_month = -everyday["Signed Amount"].sum() / months
        by_category = -everyday.groupby("Category")["Signed Amount"].sum()
        biggest = by_category.sort_values(ascending=False).head(self.n) / months
        items = [f"{category} ({amount:,.2f})" for category, amount in biggest.items()]
        saving = per_month * self.spending_cut_share
        return (
            f"You spent {per_month:,.2f} per month on everyday purchases, mostly on "
            f"{', '.join(items)}. Reducing them by {self.spending_cut_share:.0%} "
            f"saves {saving:,.2f} per month ({saving * 12:,.2f} per year)."
        )


class SubscriptionRule(AdviceRule):
    """Warn about small recurring payments that are easy to forget."""

    def __init__(self, max_monthly_cost: float = 20.0):
        self.max_monthly_cost = max_monthly_cost

    def check(self, history):
        small = [
            p
            for p in find_recurring_payments(history)
            # Subscriptions have fixed prices, so the latest price is what the
            # person will keep paying.
            if p.latest_cost <= self.max_monthly_cost
        ]
        if not small:
            return None
        names = ", ".join(p.description for p in small)
        monthly = 0
        for p in small:
            monthly += p.latest_cost
        return (
            f"You pay for small subscriptions ({names}) costing {monthly:,.2f} "
            f"per month ({monthly * 12:,.2f} per year) at current prices. "
            "Cancel the ones you rarely use."
        )


class BigExpenseRule(AdviceRule):
    """Report single one-off expenses."""

    def check(self, history):
        large = split_expenses(history)[1]
        if large.empty:
            return None
        items = [
            f"{description} ({-amount:,.2f})"
            for description, amount in zip(large["Description"], large["Signed Amount"])
        ]
        return (
            "One-off expense(s) larger than a typical month's spending: "
            f"{', '.join(items)}. Save money in advance for such expenses."
        )


class InvestmentRule(AdviceRule):
    """Suggest building an emergency fund then investing the monthly surplus.

    Default number of emergency months is set to 3.
    """

    def __init__(self, emergency_months: int = 3):
        self.emergency_months = emergency_months

    def check(self, history):
        summary = history.monthly_summary()
        monthly_surplus = summary["Net"].median()
        if monthly_surplus <= 0:
            return (
                "A typical month currently has no surplus, so there is nothing to "
                "put into an emergency fund or to invest yet. Start by lowering "
                "your costs first in order to save money."
            )
        emergency_fund = summary["Spending"].median() * self.emergency_months
        if emergency_fund == 0:
            return (
                "No spending was recorded, so an emergency fund value cannot be "
                "estimated."
            )
        months_needed = math.ceil(emergency_fund / monthly_surplus)
        return (
            f"First keep an emergency fund of {self.emergency_months} months of "
            f"typical spending ({emergency_fund:,.2f} needed to be saved). At your "
            f"typical monthly surplus of {monthly_surplus:,.2f}, this takes about "
            f"{months_needed} months if you are starting from zero. After that, "
            "consider investing the surplus regularly, for example in a "
            "diversified fund, instead of leaving it in a bank account."
        )


def give_advice(
    history: TransactionHistory, rules: list | None = None, recent_months: int = 12
) -> list:
    """Run every rule on the last recent_months months and return the messages."""
    if rules is None:
        rules = [
            SavingsRateRule(),
            RecurringPaymentsRule(),
            SubscriptionRule(),
            EverydaySpendingRule(),
            BigExpenseRule(),
            InvestmentRule(),
        ]
    recent = history.last_months(recent_months)
    messages = []
    for rule in rules:
        message = rule.check(recent)
        if message is not None:
            messages.append(message)
    return messages
