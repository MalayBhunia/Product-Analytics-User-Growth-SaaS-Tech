import random
from pathlib import Path

import numpy as np
import pandas as pd


# =========================================================
# 1. Configuration
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "subscriptions.csv"
OUTPUT_DIR = BASE_DIR / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "transactions.csv"

END_DATE = pd.Timestamp("2026-08-31")

random.seed(42)
np.random.seed(42)


# =========================================================
# 2. Plan Prices
# =========================================================

PLAN_PRICES = {
    "Free": 0.00,
    "Basic": 19.00,
    "Pro": 49.00,
    "Enterprise": 149.00
}


# =========================================================
# 3. Payment Methods
# =========================================================

PAYMENT_METHODS = [
    "Credit Card",
    "Debit Card",
    "UPI",
    "PayPal",
    "Bank Transfer"
]

PAYMENT_WEIGHTS = [
    0.35,
    0.20,
    0.25,
    0.12,
    0.08
]


# =========================================================
# 4. Transaction Types
# =========================================================

TRANSACTION_TYPES = [
    "Subscription Payment",
    "Upgrade Payment",
    "Downgrade Payment",
    "Refund"
]


# =========================================================
# 5. Load subscriptions.csv
# =========================================================

print("=" * 65)
print("TRANSACTION DATA GENERATION")
print("=" * 65)

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"subscriptions.csv not found at:\n{INPUT_FILE}"
    )


print("\nLoading subscriptions.csv...")

subscriptions = pd.read_csv(
    INPUT_FILE
)


# =========================================================
# 6. Validate columns
# =========================================================

required_columns = [
    "subscription_id",
    "user_id",
    "plan_type",
    "start_date",
    "end_date",
    "monthly_price",
    "subscription_status"
]

missing_columns = [
    col
    for col in required_columns
    if col not in subscriptions.columns
]

if missing_columns:

    raise ValueError(
        "Missing required columns:\n"
        + ", ".join(missing_columns)
    )


# =========================================================
# 7. Convert dates
# =========================================================

subscriptions["start_date"] = pd.to_datetime(
    subscriptions["start_date"],
    errors="coerce"
)

subscriptions["end_date"] = pd.to_datetime(
    subscriptions["end_date"],
    errors="coerce"
)


if subscriptions["start_date"].isna().any():

    raise ValueError(
        "Invalid start_date found."
    )


if subscriptions["end_date"].isna().any():

    raise ValueError(
        "Invalid end_date found."
    )


# =========================================================
# 8. Validate plan prices
# =========================================================

expected_prices = subscriptions["plan_type"].map(
    PLAN_PRICES
)

if not np.allclose(
    subscriptions["monthly_price"],
    expected_prices
):

    raise ValueError(
        "monthly_price does not match plan_type."
    )


print(
    f"Subscriptions loaded: "
    f"{len(subscriptions):,}"
)


# =========================================================
# 9. Generate transactions
# =========================================================

print("\nGenerating transactions...")

transaction_records = []

transaction_number = 1


for subscription in subscriptions.itertuples(
    index=False
):

    subscription_id = (
        subscription.subscription_id
    )

    user_id = subscription.user_id

    plan_type = subscription.plan_type

    start_date = pd.Timestamp(
        subscription.start_date
    )

    end_date = pd.Timestamp(
        subscription.end_date
    )

    monthly_price = float(
        subscription.monthly_price
    )

    subscription_status = (
        subscription.subscription_status
    )


    # -----------------------------------------------------
    # Free plan does not create payment transactions
    # -----------------------------------------------------

    if monthly_price <= 0:

        continue


    # -----------------------------------------------------
    # Generate monthly payment dates
    # -----------------------------------------------------

    payment_date = start_date


    while payment_date <= end_date:

        # -------------------------------------------------
        # Stop payments after project end
        # -------------------------------------------------

        if payment_date > END_DATE:
            break


        # -------------------------------------------------
        # Base payment amount
        # -------------------------------------------------

        amount = monthly_price

        transaction_type = (
            "Subscription Payment"
        )


        # -------------------------------------------------
        # Small probability of failed payment
        # -------------------------------------------------

        payment_status_random = random.random()


        if payment_status_random < 0.92:

            transaction_status = "Successful"

        elif payment_status_random < 0.97:

            transaction_status = "Failed"

        else:

            transaction_status = "Pending"


        # -------------------------------------------------
        # Payment method
        # -------------------------------------------------

        payment_method = np.random.choice(
            PAYMENT_METHODS,
            p=PAYMENT_WEIGHTS
        )


        # -------------------------------------------------
        # Rare refund
        # -------------------------------------------------

        if (
            transaction_status == "Successful"
            and random.random() < 0.015
        ):

            transaction_type = "Refund"

            amount = -round(
                amount * random.uniform(
                    0.50,
                    1.00
                ),
                2
            )


        # -------------------------------------------------
        # Transaction ID
        # -------------------------------------------------

        transaction_records.append({

            "transaction_id":
                f"TXN{transaction_number:09d}",

            "user_id":
                user_id,

            "subscription_id":
                subscription_id,

            "transaction_date":
                payment_date.date(),

            "amount":
                round(amount, 2),

            "payment_method":
                payment_method,

            "transaction_type":
                transaction_type,

            "transaction_status":
                transaction_status
        })


        transaction_number += 1


        # -------------------------------------------------
        # Move to next month
        # -------------------------------------------------

        next_payment_date = (
            payment_date
            + pd.DateOffset(months=1)
        )


        # Prevent infinite loop
        if next_payment_date <= payment_date:

            break


        payment_date = next_payment_date


# =========================================================
# 10. Create DataFrame
# =========================================================

transactions = pd.DataFrame(
    transaction_records
)


if transactions.empty:

    raise RuntimeError(
        "No transactions were generated."
    )


# =========================================================
# 11. Convert date
# =========================================================

transactions["transaction_date"] = pd.to_datetime(
    transactions["transaction_date"]
)


# =========================================================
# 12. Validation
# =========================================================

print("\nRunning validation checks...")


# Transaction ID unique
assert transactions[
    "transaction_id"
].is_unique


# Valid users
assert transactions[
    "user_id"
].isin(
    subscriptions["user_id"]
).all()


# Valid subscription IDs
assert transactions[
    "subscription_id"
].isin(
    subscriptions["subscription_id"]
).all()


# Transaction dates within project period
assert (
    transactions["transaction_date"]
    >= pd.Timestamp("2022-01-01")
).all()

assert (
    transactions["transaction_date"]
    <= END_DATE
).all()


# Transaction date must belong to subscription period
validation_df = transactions.merge(
    subscriptions[
        [
            "subscription_id",
            "start_date",
            "end_date",
            "monthly_price"
        ]
    ],
    on="subscription_id",
    how="left",
    suffixes=(
        "_transaction",
        "_subscription"
    )
)

assert (
    validation_df["transaction_date"]
    >= validation_df["start_date"]
).all()

assert (
    validation_df["transaction_date"]
    <= validation_df["end_date"]
).all()


# =========================================================
# 13. Save CSV
# =========================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

if OUTPUT_FILE.exists():

    OUTPUT_FILE.unlink()

print("\nSaving transactions.csv...")

transactions.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# 14. Final summary
# =========================================================

print("\n" + "=" * 65)
print("TRANSACTIONS DATASET CREATED SUCCESSFULLY")
print("=" * 65)

print(
    f"Total subscriptions : "
    f"{len(subscriptions):,}"
)

print(
    f"Total transactions  : "
    f"{len(transactions):,}"
)

print(
    f"Unique users        : "
    f"{transactions['user_id'].nunique():,}"
)

print(
    f"Total transaction value : "
    f"${transactions['amount'].sum():,.2f}"
)

print(
    f"Output file         : "
    f"{OUTPUT_FILE}"
)


# =========================================================
# 15. Transaction status summary
# =========================================================

print("\nTransaction status:")

status_summary = (
    transactions["transaction_status"]
    .value_counts()
)

print(
    status_summary.to_string()
)


# =========================================================
# 16. Transaction type summary
# =========================================================

print("\nTransaction type:")

type_summary = (
    transactions["transaction_type"]
    .value_counts()
)

print(
    type_summary.to_string()
)


# =========================================================
# 17. Revenue by plan
# =========================================================

print("\nRevenue by plan:")

revenue_by_plan = (
    transactions
    .merge(
        subscriptions[
            [
                "subscription_id",
                "plan_type"
            ]
        ],
        on="subscription_id",
        how="left"
    )
    .groupby("plan_type")
    .agg(
        transactions=(
            "transaction_id",
            "count"
        ),
        total_revenue=(
            "amount",
            "sum"
        )
    )
    .reset_index()
)

print(
    revenue_by_plan.to_string(
        index=False
    )
)


# =========================================================
# 18. Sample data
# =========================================================

print("\nSample transactions:")

print(
    transactions
    .head(10)
    .to_string(index=False)
)


print("\nGeneration completed successfully.")