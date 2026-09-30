"""Detects recurring payments."""

from financial_analysis_tool.transaction_history import TransactionHistory


class RecurringPayment:
    """A payment that repeats about once a month with a relatively stable amount.

    All values describe the recent months, except total_paid, which covers the
    whole history.
    """

    def __init__(
        self,
        description: str,
        category: str,
        recent_average_monthly_cost: float,
        months_paid: int,
        recent_months: int,
        latest_cost: float,
        total_paid: float,
    ):
        self.description = description
        self.category = category
        self.recent_average_monthly_cost = recent_average_monthly_cost
        self.months_paid = months_paid
        self.recent_months = recent_months
        self.latest_cost = latest_cost
        self.total_paid = total_paid

    @property
    def yearly_cost(self) -> float:
        """The amount paid per year for this recurring payment."""
        return self.recent_average_monthly_cost * 12

    def __lt__(self, other):
        # Enables the sorted() function to order payments by their
        # 'recent_average_monthly_cost'.
        return self.recent_average_monthly_cost < other.recent_average_monthly_cost

    def __repr__(self):
        return (
            f"RecurringPayment({self.description!r}, "
            f"average of {self.recent_average_monthly_cost:.2f} per month, "
            f"paid in {self.months_paid} out of the last {self.recent_months} months)"
        )


def find_recurring_payments(
    history: TransactionHistory,
    min_share_of_months: float = 0.75,
    max_payments_per_month: float = 1.1,
    max_variation: float = 0.4,
    recent_months: int = 12,
) -> list:
    """Return the recurring payments in a transaction history.

    Only the last recent_months months are used to decide whether a description
    is recurring now, so a long history with old prices or payments that started
    recently is handled correctly. A description will be considered as recurring
    if, in those recent months, it is paid in at least min_share_of_months of the
    months, with the set max_payments_per_month, and with a relatively stable
    amount. It must also have been paid in one of the last 3 months.
    The payments are then returned from most expensive to least expensive.
    """
    expenses = history.expenses.copy()
    # Create the 'Cost' column.
    expenses["Cost"] = -expenses["Signed Amount"]

    # The whole history is only used to describe each payment and to check when
    # it was last paid.
    groups = expenses.groupby("Description")
    # Since the transactions are sorted by date, the last one is the latest price
    # paid for the 'Description'.
    latest_cost = groups["Cost"].last()
    # The total amount paid overall for each 'Description'.
    total_paid = groups["Cost"].sum()
    # The last month in which each 'Description' was paid.
    last_month_paid = groups["Month"].max()

    # Only the 'recent_months' are used to decide if a payment is recurring now.
    recent_window = history.months[-recent_months:]
    recent = expenses[expenses["Month"].isin(recent_window)]
    recent_groups = recent.groupby("Description")
    recent_months_paid = recent_groups["Month"].nunique()
    payments_per_month = recent_groups.size() / recent_months_paid
    # Calculate the coefficient of variation.
    variation = (recent_groups["Cost"].std() / recent_groups["Cost"].mean()).fillna(0)
    # The average monthly cost is the mean per payment.
    recent_cost = recent_groups["Cost"].mean()

    payments = []
    for description in recent_months_paid.index:
        share = recent_months_paid[description] / len(recent_window)
        is_regular = share >= min_share_of_months
        is_monthly = payments_per_month[description] <= max_payments_per_month
        is_stable = variation[description] <= max_variation
        # A payment is active if it was paid in one of the last 3 months.
        is_active = last_month_paid[description] in history.months[-3:]
        if is_regular and is_monthly and is_stable and is_active:
            category = expenses[expenses["Description"] == description]["Category"]
            payments.append(
                RecurringPayment(
                    description,
                    category.iloc[0],
                    recent_cost[description],
                    recent_months_paid[description],
                    len(recent_window),
                    latest_cost[description],
                    total_paid[description],
                )
            )
    # Sort in descending order (more expensive first).
    return sorted(payments, reverse=True)


def total_monthly_cost(payments: list) -> float:
    """Return the combined monthly cost of a list of recurring payments."""
    total = 0
    for payment in payments:
        total += payment.recent_average_monthly_cost
    return total
