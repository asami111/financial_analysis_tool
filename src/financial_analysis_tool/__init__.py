"""Financial Analysis Tool: analyze a personal transaction history."""

from financial_analysis_tool.data_load_and_clean import (
    load_transactions,
    remove_transfers,
)
from financial_analysis_tool.transaction_history import TransactionHistory
from financial_analysis_tool.recurring_payments import (
    RecurringPayment,
    find_recurring_payments,
    total_monthly_cost,
)
from financial_analysis_tool.forecast import BalanceForecast
from financial_analysis_tool.recommendations import (
    AdviceRule,
    EverydaySpendingRule,
    InvestmentRule,
    BigExpenseRule,
    RecurringPaymentsRule,
    SavingsRateRule,
    SubscriptionRule,
    give_advice,
    split_expenses,
)
from financial_analysis_tool.plots import (
    plot_balance,
    plot_monthly_income_and_spending,
    plot_recurring_payments,
    plot_spending_by_category,
    save_all_plots,
)

__all__ = [
    "load_transactions",
    "remove_transfers",
    "TransactionHistory",
    "RecurringPayment",
    "find_recurring_payments",
    "total_monthly_cost",
    "BalanceForecast",
    "AdviceRule",
    "SavingsRateRule",
    "RecurringPaymentsRule",
    "SubscriptionRule",
    "EverydaySpendingRule",
    "BigExpenseRule",
    "InvestmentRule",
    "give_advice",
    "split_expenses",
    "plot_monthly_income_and_spending",
    "plot_spending_by_category",
    "plot_recurring_payments",
    "plot_balance",
    "save_all_plots",
]