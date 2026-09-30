"""Command-line interface: uv run -m financial_analysis_tool <command> [options]."""

import math
import sys

from financial_analysis_tool.forecast import BalanceForecast
from financial_analysis_tool.recommendations import give_advice
from financial_analysis_tool.recurring_payments import (
    find_recurring_payments,
    total_monthly_cost,
)
from financial_analysis_tool.transaction_history import TransactionHistory
from financial_analysis_tool.plots import save_all_plots

USAGE = """Usage: uv run -m financial_analysis_tool <command> [options]

Commands:
  summary              Total income and spending, monthly statistics
                       and the biggest spending categories.
  recurring            Detected bills and subscriptions.
  forecast             Predicted balance for the next months.
  advice               Textual recommendations for saving and investing.
  plots                Save all charts as PNG files into plots/.
  report               All of the above.
  help                 Show this message.

Options:
  --balance AMOUNT     Your current balance (default 0).
  --months N           Number of months to forecast, 1 to 120 (default 12).
  --file PATH          Analyze your own CSV file instead of the bundled data.
  --date-format FORMAT Date format of your file (default %m/%d/%Y).

Example:
  uv run -m financial_analysis_tool report --balance 5000
"""

COMMANDS = ("summary", "recurring", "forecast", "advice", "plots", "report")
# A forecast of more than 10 years is not meaningful.
MAX_MONTHS = 120


def print_heading(title: str):
    """Print a title with a line under it (for better format)."""
    print()
    print(title)
    print("-" * len(title))


def print_summary(history: TransactionHistory):
    """Print totals, monthly statistics and the top spending categories."""
    print_heading("Summary")
    print(history)
    # Align values to the right.
    print(f"Total income:   {history.total_income:12,.2f}")
    print(f"Total spending: {history.total_spending:12,.2f}")
    print(f"Net:            {history.net:12,.2f}")

    print_heading("Monthly statistics")
    print(history.monthly_statistics().round(2).to_string())

    top_items = history.spending_by_category().head(5)
    print_heading(f"Top {len(top_items)} spending categories")
    for category, amount in top_items.items():
        # Align categories to the left.
        print(f"{category:<25}{amount:12,.2f}")


def print_recurring(history: TransactionHistory):
    """Print every recurring payment and their total."""
    print_heading("Recurring payments")
    payments = find_recurring_payments(history)
    if not payments:
        print("No recurring payments found.")
        return
    window = payments[0].recent_months
    print(
        "Bills and subscriptions paid almost each month in the last "
        f"{window} months:"
    )
    print(
        f"{'Payment':<28}{'Avg/month':>11}{'Latest':>11}"
        f"{'Months':>8}{'Total paid (all time)':>22}"
    )
    for p in payments:
        months = f"{p.months_paid}/{p.recent_months}"
        print(
            f"{p.description:<28}{p.recent_average_monthly_cost:11,.2f}"
            f"{p.latest_cost:11,.2f}{months:>8}{p.total_paid:22,.2f}"
        )
    print(f"Months: in how many of the last {window} months the payment was made.")
    print("Total paid (all time): the sum of all payments in the whole history.")
    total = total_monthly_cost(payments)
    print(f"Total cost of recurring payments per month: {total:,.2f}")


def print_forecast(history: TransactionHistory, balance: float, months: int):
    """Print the predicted balance for the next 'months'."""
    forecast = BalanceForecast(history, balance)
    unit = "month" if months == 1 else "months"
    print_heading(f"Forecast for the next {months} {unit}")
    print(f"Starting balance:        {balance:12,.2f}")
    print(
        f"Typical monthly net:     {forecast.monthly_net:12,.2f} "
        f"(median of the last {forecast.recent_months} months)"
    )
    print()
    print(f"{'Month':<25}{'Balance':>12}")
    table = forecast.predict(months)
    for month, value in zip(table["Month"], table["Balance"]):
        print(f"{month:<25}{value:12,.2f}")
    print("This assumes a typical future without sudden big one-off expenses.")


def print_advice(history: TransactionHistory):
    """Print the numbered recommendations."""
    print_heading("Recommendations")
    for number, message in enumerate(give_advice(history), start=1):
        print(f"{number}. {message}")


def print_plots(history: TransactionHistory, balance: float, months: int):
    """Save all charts and print where they were saved."""
    print_heading("Charts")
    try:
        paths = save_all_plots(history, starting_balance=balance, months=months)
    # For example, there is no permission to write.
    except OSError as error:
        print(f"Error: the charts could not be saved: {error}")
        return
    for path in paths:
        print(f"Saved {path}")


def pop_option(args: list, name: str) -> str | None:
    """Remove an option like --file PATH from args and return its value.

    Returns None if the option is not given. Raises ValueError if the
    option is given without a value or more than once.
    """
    if name not in args:
        return None
    position = args.index(name)
    # The value must exist and must not be the next option.
    if position + 1 >= len(args) or args[position + 1].startswith("--"):
        raise ValueError(f"{name} needs a value")
    # Remove the option name, e.g. "--file".
    args.pop(position)
    # Remove and keep the option value, e.g. the file path.
    value = args.pop(position)
    if name in args:
        raise ValueError(f"{name} was given more than once")
    return value


def to_number(text: str | None, default: float) -> float:
    """Return text as a number (float), or default if text is None."""
    if text is None:
        return default
    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"{text!r} is not a number")
    # float() also accepts "nan" and "inf", which I will reject.
    if not math.isfinite(value):
        raise ValueError(f"{text!r} is not a number")
    return value


def main(args: list | None = None):
    """Run the command given on the command line."""
    if args is None:
        args = sys.argv[1:]
    args = args.copy()

    # Options are removed from args first, so only the command is left.
    try:
        path = pop_option(args, "--file")
        date_format = pop_option(args, "--date-format")
        if date_format is not None and path is None:
            raise ValueError("--date-format only works together with --file")
        balance = to_number(pop_option(args, "--balance"), 0.0)
        months = to_number(pop_option(args, "--months"), 12)
        if months < 1 or months > MAX_MONTHS or months != int(months):
            raise ValueError(f"--months must be a whole number from 1 to {MAX_MONTHS}")
        months = int(months)
    except ValueError as error:
        print(f"Error: {error}")
        return

    # Print USAGE (help) if needed or if no input is entered by the user.
    if not args or args[0] == "help" or "--help" in args or "-h" in args:
        print(USAGE)
        return

    command = args[0]
    # First argument must be in COMMANDS.
    if command not in COMMANDS:
        print(f"Unknown command {command!r}.")
        print(USAGE)
        return
    # Anything left after the command is not allowed
    # since the options are already popped.
    if len(args) > 1:
        if args[1].startswith("--"):
            print(f"Error: unknown option {args[1]!r}. See the list with: help")
        else:
            print(
                f"Error: unexpected {args[1]!r}. "
                "Give numbers as options, e.g. --balance 5000 --months 6."
            )
        return

    try:
        if path is None:
            history = TransactionHistory.from_csv()
        elif date_format is None:
            history = TransactionHistory.from_csv(path)
        else:
            history = TransactionHistory.from_csv(path, date_format)
    # OSError covers a missing file, a folder instead of a file and no permission.
    except (OSError, ValueError) as error:
        print(f"Error: {error}")
        return

    match command:
        case "summary":
            print_summary(history)
        case "recurring":
            print_recurring(history)
        case "forecast":
            print_forecast(history, balance, months)
        case "advice":
            print_advice(history)
        case "plots":
            print_plots(history, balance, months)
        case "report":
            print_summary(history)
            print_recurring(history)
            print_forecast(history, balance, months)
            print_advice(history)
            print_plots(history, balance, months)


if __name__ == "__main__":
    main()