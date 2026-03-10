"""Utility functions for the student expense tracker.

This module provides helper functions to load expense data, add new expenses,
compute summary statistics and category breakdowns, and perform simple budget
calculations. It is designed to be used by the Streamlit app as well as in
stand‑alone scripts or notebooks.

The functions operate on pandas DataFrame objects with the following columns:

* ``expense_name`` – a short description of the expense
* ``amount`` – the expense amount in the local currency (float)
* ``category`` – a category string (e.g. "Rent", "Groceries", "Transport", etc.)
* ``date`` – a datetime64 or string representing the date of the transaction
* ``payment_method`` – method used to pay for the expense (e.g. "Card")
* ``notes`` – optional notes or comments

The ``load_data`` function accepts a CSV path and parses the ``date`` column
into pandas datetimes. Additional helper functions summarise the data by
month or category and calculate budget related metrics.
"""

from __future__ import annotations

import pandas as pd
from typing import Tuple


def load_data(file_path: str) -> pd.DataFrame:
    """Load expense data from a CSV file.

    Parameters
    ----------
    file_path : str
        Path to the CSV file containing expense data.

    Returns
    -------
    pd.DataFrame
        A DataFrame with a parsed ``date`` column and original ordering.
    """
    df = pd.read_csv(file_path)
    # Parse date column if present
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df



def add_expense(
    df: pd.DataFrame,
    expense_name: str,
    amount: float,
    category: str,
    date: pd.Timestamp,
    payment_method: str,
    notes: str = "",
) -> pd.DataFrame:
    """Return a new DataFrame with an additional expense row.

    This function creates a copy of the provided DataFrame with a new
    transaction appended. The original DataFrame is not modified.

    Parameters
    ----------
    df : pd.DataFrame
        Existing expenses.
    expense_name : str
        A short name or description of the expense.
    amount : float
        The expense amount.
    category : str
        Category for the expense.
    date : pd.Timestamp
        The date of the expense.
    payment_method : str
        Payment method used.
    notes : str, optional
        Optional notes or comments, by default "".

    Returns
    -------
    pd.DataFrame
        New DataFrame including the appended expense.
    """
    new_row = {
        'expense_name': expense_name,
        'amount': amount,
        'category': category,
        'date': pd.to_datetime(date),
        'payment_method': payment_method,
        'notes': notes,
    }
    return pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)



def compute_monthly_totals(df: pd.DataFrame) -> pd.Series:
    """Compute total spent per month.

    Parameters
    ----------
    df : pd.DataFrame
        Expense data with a ``date`` column.

    Returns
    -------
    pd.Series
        Total spend per month indexed by period (YYYY‑MM).
    """
    if df.empty:
        return pd.Series(dtype=float)
    monthly = df.copy()
    monthly['month'] = monthly['date'].dt.to_period('M')
    return monthly.groupby('month')['amount'].sum()



def compute_category_totals(df: pd.DataFrame) -> pd.Series:
    """Compute total spent per category.

    Parameters
    ----------
    df : pd.DataFrame
        Expense data with a ``category`` column.

    Returns
    -------
    pd.Series
        Total spend per category.
    """
    if df.empty:
        return pd.Series(dtype=float)
    return df.groupby('category')['amount'].sum().sort_values(ascending=False)



def calculate_budget_metrics(df: pd.DataFrame, budget: float) -> Tuple[float, float, bool]:
    """Calculate summary metrics against a budget.

    Given a total budget, this returns the total spent, remaining budget,
    and a boolean indicating whether the budget has been exceeded.

    Parameters
    ----------
    df : pd.DataFrame
        Expense data with an ``amount`` column.
    budget : float
        The budget for the period.

    Returns
    -------
    Tuple[float, float, bool]
        (total_spent, remaining, overspending)
    """
    total_spent = df['amount'].sum() if not df.empty else 0.0
    remaining = budget - total_spent
    overspending = remaining < 0
    return total_spent, remaining, overspending



def compute_average_weekly_spend(df: pd.DataFrame) -> float:
    """Compute the average spend per week in the data.

    Parameters
    ----------
    df : pd.DataFrame
        Expense data with a ``date`` column.

    Returns
    -------
    float
        The average weekly spend. Returns 0.0 for empty data.
    """
    if df.empty:
        return 0.0
    start_date = df['date'].min()
    end_date = df['date'].max()
    num_weeks = ((end_date - start_date).days / 7) or 1
    total_spent = df['amount'].sum()
    return total_spent / num_weeks
