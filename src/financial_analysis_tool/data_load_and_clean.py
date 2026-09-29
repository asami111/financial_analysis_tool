"""Load and clean transactions data from a CSV file.

The dataset comes from Kaggle
(https://www.kaggle.com/datasets/bukolafatunde/personal-finance).
It stores every amount as a positive number and uses the "Transaction Type" column,
which has the values "debit" or "credit" to tell expenses from income,
where debit is expenses and credit is income.
"""

import os

import pandas as pd

# The data folder exists next to this file. Building the path from __file__
# ensures that the CSV file is found no matter which folder the program is run from.
DATA_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "data", "personal_transactions.csv"
)

REQUIRED_COLUMNS = [
    "Date",
    "Description",
    "Amount",
    "Transaction Type",
    "Category",
    "Account Name",
]

# Paying off a credit card from the checking account moves money between
# the person's own accounts. It will considered as neither net income, nor net spending.
TRANSFER_DESCRIPTION = "Credit Card Payment"


def load_transactions(path: str = DATA_FILE_PATH, date_format: str = "%m/%d/%Y",
    include_transfers: bool = False,) -> pd.DataFrame:
    """Load transactions from a CSV file and prepare them for analysis.
    The function takes the path for the dataset as an input, if not provided then
    it runs on the default dataset path stated.
    It also takes the preferred date format as an input parameter, if not provided then it
    takes the default date format stated, since this is the one used by my own used dataset.
    It also has include_transfers option that toggles if the user
    wants to include TRANSFER_DESCRIPTION = 'Credit Card Payment' in some computations,
    since paying off a credit card from the checking account moves money between
    the person's own accounts. The user may want to consider it as neither net income,
    nor net spending, which is my default case and the case I will mainly
    consider throughout my program, but the option will still be there in
    the tool for the user to choose.
    The function checks if there are missing columns or unknown transaction types other than
    'debit' or 'credit' and raises an exception accordingly.
    """

    df = pd.read_csv(path)

    missing_columns = []

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    unknown_transaction_types = set(df["Transaction Type"]) - {"debit", "credit"}
    if unknown_transaction_types:
        raise ValueError(f"Unknown transaction types: {unknown_transaction_types}")

    # Turn the date strings into real dates so they can be sorted.
    try:
        df["Date"] = pd.to_datetime(df["Date"], format=date_format)
    except ValueError:
        raise ValueError(
            f"Dates do not match the format {date_format!r}. "
            "Please pass the right date format."
        )
    # Creating the 'Month' column.
    df["Month"] = df["Date"].dt.strftime("%Y-%m")

    # Creating the 'Signed Amount' column, where 'Transaction Type' with 'debit' value
    # will have their 'Signed Amount' to be equal the negative 'Amount' value.
    df["Signed Amount"] = df["Amount"]

    # is_debit identifies which observations are expenses.
    is_debit = df["Transaction Type"] == "debit"
    df.loc[is_debit, "Signed Amount"] = -df.loc[is_debit, "Amount"]

    if not include_transfers:
        df = remove_transfers(df)

    return df.sort_values("Date").reset_index(drop=True)


def remove_transfers(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the transactions without credit card payments."""
    return df[df["Description"] != TRANSFER_DESCRIPTION].reset_index(drop=True)