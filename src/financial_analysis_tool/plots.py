"""Create charts of a transaction history and save them as PNG files.

The charts are only saved, never shown in a window, so the tool also
works on machines without a screen.
"""

import math
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import StrMethodFormatter

from financial_analysis_tool.forecast import BalanceForecast
from financial_analysis_tool.recurring_payments import find_recurring_payments
from financial_analysis_tool.transaction_history import TransactionHistory

DEFAULT_OUTPUT_DIR = "plots"
LABEL_SIZE = 12
TITLE_SIZE = 14
# For the plot's x-axis to be clear.
MAX_MONTH_LABELS = 24


def _save(fig, output_dir: str, filename: str) -> str:
    """Save a figure into output_dir, close it and return the file path."""
    os.makedirs(output_dir, exist_ok=True)
    # Join path based on OS convention.
    path = os.path.join(output_dir, filename)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def _label_months(ax, months: list):
    """Label at most MAX_MONTH_LABELS months on the x-axis."""
    # Keep the step at least 1, also for an empty list of months.
    step = max(1, math.ceil(len(months) / MAX_MONTH_LABELS))
    ax.set_xticks(months[::step])
    # Display x-axis text vertically to save space.
    ax.tick_params(axis="x", labelrotation=90)


def _show_message(ax, message: str):
    """Write a message in the middle of an empty chart instead of empty axes."""
    # transAxes: (0.5, 0.5) means the middle of the chart area.
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        fontsize=LABEL_SIZE,
        transform=ax.transAxes,
    )
    ax.set_axis_off()


def plot_monthly_income_and_spending(
    history: TransactionHistory, output_dir: str = DEFAULT_OUTPUT_DIR
) -> str:
    """Plot income and spending for every month as a line chart."""
    summary = history.monthly_summary()
    months = list(summary.index)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(months, summary["Income"], "o-", ms=4, color="green", label="Income")
    ax.plot(months, summary["Spending"], "o-", ms=4, color="red", label="Spending")
    ax.set_xlabel("Month", fontsize=LABEL_SIZE)
    ax.set_ylabel("Amount", fontsize=LABEL_SIZE)
    ax.set_title("Monthly income and spending", fontsize=TITLE_SIZE)
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    _label_months(ax, months)
    ax.legend(fontsize=LABEL_SIZE)
    return _save(fig, output_dir, "monthly_income_and_spending.png")


def plot_spending_by_category(
    history: TransactionHistory,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    top: int = 10,
) -> str:
    """Plot the total spending of the top categories as horizontal bars.

    The bars are chosen to be horizontal for better displayability
    of the category names.
    """

    # Reverse the order so the largest category is drawn at the top,
    # since 'barh()' usually starts from the bottom.
    spending = history.spending_by_category().head(top)[::-1]
    fig, ax = plt.subplots(figsize=(10, 5))
    if spending.empty:
        _show_message(ax, "No spending found")
    else:
        ax.barh(spending.index, spending.values, color="blue")
        ax.set_xlabel("Total spending", fontsize=LABEL_SIZE)
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.set_title(f"Top {len(spending)} spending categories", fontsize=TITLE_SIZE)
    return _save(fig, output_dir, "spending_by_category.png")


def plot_recurring_payments(
    history: TransactionHistory, output_dir: str = DEFAULT_OUTPUT_DIR
) -> str:
    """Plot the average monthly cost of every recurring payment as horizontal bars."""
    # Largest recurring payment is drawn at the top.
    payments = sorted(find_recurring_payments(history))
    fig, ax = plt.subplots(figsize=(10, 5))
    if not payments:
        _show_message(ax, "No recurring payments found")
    else:
        names = [p.description for p in payments]
        costs = [p.recent_average_monthly_cost for p in payments]
        window = payments[0].recent_months
        ax.barh(names, costs, color="darkorange")
        ax.set_xlabel(
            f"Average cost per month over the last {window} months",
            fontsize=LABEL_SIZE,
        )
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.set_title("Recurring payments", fontsize=TITLE_SIZE)
    return _save(fig, output_dir, "recurring_payments.png")


def plot_balance(
    history: TransactionHistory,
    starting_balance: float = 0.0,
    months: int = 12,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> str:
    """Plot the savings so far and the forecast balance beside each other."""
    summary = history.monthly_summary()
    past_months = list(summary.index)
    saved_so_far = np.cumsum(summary["Net"].values)
    forecast = BalanceForecast(history, starting_balance).predict(months)
    future_months = list(forecast["Month"])

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot(past_months, saved_so_far, "o-", ms=4, color="purple")
    axes[0].axhline(0, color="gray", linewidth=1)
    axes[0].set_xlabel("Month", fontsize=LABEL_SIZE)
    axes[0].set_ylabel("Total saved", fontsize=LABEL_SIZE)
    axes[0].set_title("Savings so far", fontsize=TITLE_SIZE)
    axes[0].yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    _label_months(axes[0], past_months)

    axes[1].plot(future_months, forecast["Balance"], "o--", ms=4, color="black")
    axes[1].set_xlabel("Month", fontsize=LABEL_SIZE)
    axes[1].set_ylabel("Balance", fontsize=LABEL_SIZE)
    axes[1].set_title(
        f"Forecast from a starting balance of {starting_balance:,.0f}",
        fontsize=TITLE_SIZE,
    )
    axes[1].yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    _label_months(axes[1], future_months)

    return _save(fig, output_dir, "balance.png")


def save_all_plots(
    history: TransactionHistory,
    starting_balance: float = 0.0,
    months: int = 12,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> list:
    """Create every chart and return the paths of the saved files."""
    return [
        plot_monthly_income_and_spending(history, output_dir),
        plot_spending_by_category(history, output_dir),
        plot_recurring_payments(history, output_dir),
        plot_balance(history, starting_balance, months, output_dir),
    ]
