"""
Streamlit application for the Student Expense Tracker Dashboard.

This app allows users to track their expenses, compare spending by
category and month, monitor budget usage, and derive practical insights.
It is intentionally lightweight to make it easy to run on a local
machine without additional services. Data can be loaded from the provided
sample CSV file or from a user‑uploaded CSV. Users can also append new
expenses during a session (data is stored in session state but not
persisted to disk).

Usage::

    pip install -r requirements.txt
    streamlit run streamlit_app.py

"""

from __future__ import annotations

import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from expense_utils import (
    load_data,
    add_expense,
    compute_monthly_totals,
    compute_category_totals,
    calculate_budget_metrics,
    compute_average_weekly_spend,
)


DATA_PATH = Path("data/sample_expenses.csv")


def get_initial_data() -> pd.DataFrame:
    """Load the default sample dataset.

    Returns a DataFrame from the ``DATA_PATH``. If the file does
    not exist, returns an empty DataFrame with the appropriate columns.
    """
    if DATA_PATH.exists():
        return load_data(str(DATA_PATH))
    return pd.DataFrame(
        columns=["expense_name", "amount", "category", "date", "payment_method", "notes"]
    )


def main() -> None:
    st.set_page_config(page_title="Student Expense Tracker", layout="wide")
    st.title("\ud83d\udcca Student Expense Tracker Dashboard")

    # Sidebar: file upload and budget setting
    st.sidebar.header("Configuration")
    uploaded_file = st.sidebar.file_uploader(
        "Upload your expenses CSV", type=["csv"], accept_multiple_files=False
    )

    # Load data
    if "expenses" not in st.session_state:
        if uploaded_file is not None:
            st.session_state["expenses"] = load_data(uploaded_file)
        else:
            st.session_state["expenses"] = get_initial_data()

    df = st.session_state["expenses"].copy()

    # Set budget
    default_budget = float(df["amount"].sum() * 1.2) if not df.empty else 1000.0
    budget = st.sidebar.number_input(
        "Monthly budget", min_value=0.0, value=round(default_budget, 2), step=10.0
    )

    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigate", (
            "Overview",
            "Add Expense",
            "View Expenses",
            "Category Analysis",
            "Monthly Trend",
            "Insights",
        ),
    )

    # Add Expense page
    if page == "Add Expense":
        st.subheader("Add a new expense")
        with st.form(key="add_expense_form"):
            c1, c2 = st.columns(2)
            expense_name = c1.text_input("Expense name", value="")
            amount = c2.number_input("Amount", min_value=0.0, step=1.0)
            category = c1.selectbox(
                "Category",
                [
                    "Rent",
                    "Groceries",
                    "Utilities",
                    "Transport",
                    "Dining",
                    "Entertainment",
                    "Healthcare",
                    "Education",
                    "Miscellaneous",
                ],
            )
            date = c2.date_input("Date", value=datetime.date.today())
            payment_method = c1.selectbox(
                "Payment method", ["Card", "Cash", "Mobile", "Other"]
            )
            notes = st.text_area("Notes", value="", height=50)
            submit = st.form_submit_button("Add Expense")

        if submit:
            # Append new expense to session state
            st.session_state["expenses"] = add_expense(
                df,
                expense_name,
                amount,
                category,
                pd.to_datetime(date),
                payment_method,
                notes,
            )
            st.success("Expense added successfully!")
            # Refresh df to include new entry
            df = st.session_state["expenses"].copy()

    # View Expenses page
    if page == "View Expenses":
        st.subheader("All expenses")
        if df.empty:
            st.info("No expenses to display. Add some expenses first.")
        else:
            # Filters
            with st.expander("Filter options"):
                col1, col2, col3 = st.columns(3)
                category_filter = col1.multiselect(
                    "Category", options=df["category"].unique().tolist(), default=[]
                )
                start_date = col2.date_input(
                    "Start date", value=df["date"].min().date() if not df.empty else datetime.date.today()
                )
                end_date = col3.date_input(
                    "End date", value=df["date"].max().date() if not df.empty else datetime.date.today()
                )

            filtered_df = df.copy()
            if category_filter:
                filtered_df = filtered_df[filtered_df["category"].isin(category_filter)]
            filtered_df = filtered_df[
                (filtered_df["date"].dt.date >= start_date)
                & (filtered_df["date"].dt.date <= end_date)
            ]
            st.dataframe(filtered_df.sort_values("date", ascending=False), use_container_width=True)

    # Category Analysis page
    if page == "Category Analysis":
        st.subheader("Spend by category")
        if df.empty:
            st.info("No data available.")
        else:
            category_totals = compute_category_totals(df)
            st.bar_chart(category_totals)
            # Top categories insight
            if not category_totals.empty:
                top_cat = category_totals.idxmax()
                st.markdown(
                    f"**Top spending category:** {top_cat} (\u00a3{category_totals[top_cat]:.2f})"
                )

    # Monthly Trend page
    if page == "Monthly Trend":
        st.subheader("Monthly spending trend")
        if df.empty:
            st.info("No data available.")
        else:
            monthly_totals = compute_monthly_totals(df)
            # Convert period index to string for plotting
            monthly_totals.index = monthly_totals.index.astype(str)
            st.line_chart(monthly_totals)
            if not monthly_totals.empty:
                peak_month = monthly_totals.idxmax()
                st.markdown(
                    f"**Highest spending month:** {peak_month} (\u00a3{monthly_totals[peak_month]:.2f})"
                )

    # Overview page
    if page == "Overview":
        st.subheader("Summary overview")
        if df.empty:
            st.info("No expenses recorded yet.")
        else:
            total_spent, remaining, overspend = calculate_budget_metrics(df, budget)
            avg_weekly = compute_average_weekly_spend(df)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total spent", f"\u00a3{total_spent:.2f}")
            col2.metric("Remaining budget", f"\u00a3{remaining:.2f}", delta=None)
            col3.metric(
                "Budget status",
                "Over budget" if overspend else "Within budget",
                delta=None,
            )
            col4.metric("Avg weekly spend", f"\u00a3{avg_weekly:.2f}")

            # Show pie/bar of category breakdown
            category_totals = compute_category_totals(df)
            st.bar_chart(category_totals)

    # Insights page
    if page == "Insights":
        st.subheader("Insights and recommendations")
        if df.empty:
            st.info("No data available to generate insights.")
        else:
            # Compute key insights
            category_totals = compute_category_totals(df)
            monthly_totals = compute_monthly_totals(df)
            total_spent, remaining, overspend = calculate_budget_metrics(df, budget)
            avg_weekly = compute_average_weekly_spend(df)

            # Top spending category
            if not category_totals.empty:
                top_category = category_totals.idxmax()
                top_value = category_totals.max()
                st.markdown(
                    f"- **Top spending category**: {top_category} (\u00a3{top_value:.2f})"
                )

            # Peak month
            if not monthly_totals.empty:
                peak_month = monthly_totals.idxmax()
                st.markdown(
                    f"- **Peak spending month**: {peak_month} (\u00a3{monthly_totals[peak_month]:.2f})"
                )

            # Budget status
            if overspend:
                st.markdown(
                    f"- **Budget alert**: You are over budget by \u00a3{abs(remaining):.2f}. Consider reducing discretionary spendings."
                )
            else:
                st.markdown(
                    f"- **Budget status**: You have \u00a3{remaining:.2f} remaining. Great job staying within budget!"
                )

            # Additional suggestions
            st.markdown("\n**Suggestions:**")
            st.markdown(
                "- Review high\u2011cost categories and look for ways to reduce spending."
            )
            st.markdown(
                "- Compare weekly averages across months to identify seasonal trends."
            )
            st.markdown(
                "- Set separate sub\u2011budgets for essentials (rent, groceries) and discretionary items."
            )

    # Footer
    st.caption("Built with Streamlit. Data stored in session during runtime; to persist your data, export and reload the CSV.")


if __name__ == "__main__":
    main()
