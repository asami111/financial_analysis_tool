"""A class that holds a transaction history and holds data about it."""

import pandas as pd

from financial_analysis_tool.data_load_and_clean import (
    DATA_FILE_PATH,
    load_transactions,
)


class TransactionHistory:
    """A person's transactions with methods and properties to summarize them."""

    def __init__(self, transactions: pd.DataFrame):
        self.transactions = transactions

    @classmethod
    def from_csv(cls, path: str = DATA_FILE_PATH, date_format: str = "%m/%d/%Y"):
        # Creating the TransactionHistory from the CSV file.
        return cls(load_transactions(path, date_format))

    def __len__(self):
        return len(self.transactions)

    # Here I display the date as YYYY-MM-DD, in order to be unambiguous.
    def __repr__(self):
        start = self.transactions["Date"].min().strftime("%Y-%m-%d")
        end = self.transactions["Date"].max().strftime("%Y-%m-%d")
        return f"TransactionHistory({len(self)} transactions, {start} to {end})"

    @property
    def income(self) -> pd.DataFrame:
        # Returns the income transactions.
        return self.transactions[self.transactions["Signed Amount"] > 0]

    @property
    def expenses(self) -> pd.DataFrame:
        # Returns the spending transactions.
        return self.transactions[self.transactions["Signed Amount"] < 0]

    @property
    def total_income(self) -> float:
        # The sum of all income.
        return self.income["Signed Amount"].sum()

    @property
    def total_spending(self) -> float:
        # The sum of all expenses (displayed as a positive number).
        return -self.expenses["Signed Amount"].sum()

    @property
    def net(self) -> float:
        # Total income minus total spending.
        return self.total_income - self.total_spending

    @property
    def months(self) -> list:
        # Returns all months appearing in the history and sorts them.
        return sorted(self.transactions["Month"].unique())

    def monthly_summary(self) -> pd.DataFrame:
        """Return income, spending and net for every month and fills NaN values with zeros."""
        income = self.income.groupby("Month")["Signed Amount"].sum()
        # Here expenses will be shown as positive.
        spending = -self.expenses.groupby("Month")["Signed Amount"].sum()
        summary = pd.DataFrame({"Income": income, "Spending": spending})
        """ Reorders by month and adds missing months in the summary DataFrame, 
         as well as filling NaN values in the summary DataFrame with zero. """
        summary = summary.reindex(self.months).fillna(0)
        # Create 'Net' column in the summary DataFrame.
        summary["Net"] = summary["Income"] - summary["Spending"]
        return summary

    def monthly_statistics(self) -> pd.DataFrame:
        """Returns the mean, median, min and max of the monthly income, spending and net."""

        summary = self.monthly_summary()
        return pd.DataFrame(
            {
                "Mean": summary.mean(),
                "Median": summary.median(),
                "Min": summary.min(),
                "Max": summary.max(),
            }
        )

    def spending_by_category(self) -> pd.Series:
        """Returns the total spending per category, in descending order (largest first).
        Expenses are displayed in positive values here."""
        spending = -self.expenses.groupby("Category")["Signed Amount"].sum()
        return spending.sort_values(ascending=False)

    def spending_by_description(self, n: int = 5) -> pd.Series:
        """Returns the n Descriptions with the highest total spending, in descending
         order (largest first).
         Expenses are also displayed in positive values here."""
        spending = -self.expenses.groupby("Description")["Signed Amount"].sum()
        return spending.sort_values(ascending=False).head(n)