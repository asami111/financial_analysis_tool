# Financial Analysis Tool

A command-line tool that analyzes a history of bank transactions. It detects recurring payments, predicts the future account balance and gives textual recommendations for saving and investing.

A sample dataset is included, so the tool works right after installation.

## Installation

Requires [uv](https://docs.astral.sh/uv/) and git.

```bash
git clone https://github.com/asami111/financial_analysis_tool.git
cd financial_analysis_tool
uv venv
uv pip install -e .
```

## Usage

Run the full analysis with a current balance of 5,000 for example:

```bash
uv run -m financial_analysis_tool report --balance 5000
```

Other commands:

```bash
uv run -m financial_analysis_tool summary                              # income, spending and top categories
uv run -m financial_analysis_tool recurring                            # recurring bills and subscriptions
uv run -m financial_analysis_tool forecast --balance 5000 --months 6   # balance for the next 6 months
uv run -m financial_analysis_tool advice                               # recommendations
uv run -m financial_analysis_tool plots --balance 5000 --months 6      # save the charts
uv run -m financial_analysis_tool help                                 # all commands and options
```

`--balance` is your current balance (default 0) and `--months` the number of months to forecast (default 12). Both can be added to any command, in any order.

To analyze your own transactions, add `--file my_bank.csv` to your command. The file needs the columns `Date`, `Description`, `Amount`, `Transaction Type` (`debit` or `credit`), `Category` and `Account Name`. If the dates are not written like `01/31/2018`, also add their format, for example `--date-format %Y-%m-%d`.

The categories' names in your file can be anything. They are only used to label the results.

## Output files

The `plots` command saves four charts into the `plots/` folder. The charts in this repository were created with `uv run -m financial_analysis_tool plots --balance 5000`.

- [`monthly_income_and_spending.png`](plots/monthly_income_and_spending.png): income and spending per month
- [`spending_by_category.png`](plots/spending_by_category.png): total spending per category
- [`recurring_payments.png`](plots/recurring_payments.png): the monthly cost of each recurring payment
- [`balance.png`](plots/balance.png): savings so far and the balance forecast

## Example notebook

[`notebooks/example_usage.ipynb`](notebooks/example_usage.ipynb) shows how to use the package from Python: loading data, the summary, recurring payments, the forecast, the recommendations, and the charts.

## How it works

- **Recurring payments** are payments that are paid about once a month with a stable amount in at least 75% of the last 12 months, and at least once in the last 3 months.
- **The forecast** adds the median monthly net of the last 12 months to the balance each month. The median is used instead of the mean because a few months contain very large one-off expenses, such as the home improvement payment of 9,200.00 in 6/20/2019, which greatly alters the mean but not the median. The `summary` command shows this effect: over the whole history, the mean monthly net is 1462.27, the median 1910.56 and the lowest month -6912.38. In addition, less than two years of data are not enough to reliably learn a trend or a yearly pattern (apply advanced ML methods), so a robust typical value is the most reasonable basis for the forecast.
- **The forecast** assumes a typical future. It does not include sudden one-off expenses or future changes in pay.
- **The recommendations** split the spending of the last 12 months into recurring payments, one-off expenses (single payments larger than a typical month's spending) and everyday purchases (everything else), and give advice that fits each: switch provider or renegotiate large contracts, cancel unused subscriptions, reduce everyday purchases and save in advance for large projects. They also compare the savings rate with a 20% target and suggest building an emergency fund before investing.
- **Credit card payments** are ignored, because they only move money between the person's checking account to the person's credit cards.

## Data

The sample data is the [Personal Finance dataset](https://www.kaggle.com/datasets/bukolafatunde/personal-finance) by bukolafatunde on Kaggle. It covers January 2018 to September 2019 and includes a checking account and two credit cards.

## License

MIT, see [LICENSE](LICENSE).
