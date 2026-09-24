import random
from pathlib import Path

import numpy as np
import pandas as pd


# =========================================================
# 1. Configuration
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "users.csv"
OUTPUT_DIR = BASE_DIR / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "subscriptions.csv"

START_DATE = pd.Timestamp("2022-01-01")
END_DATE = pd.Timestamp("2026-08-31")

# Reproducibility
random.seed(42)
np.random.seed(42)


# =========================================================
# 2. Plan Configuration
# =========================================================

PLAN_PRICES = {
    "Free": 0,
    "Basic": 19,
    "Pro": 49,
    "Enterprise": 149
}

PLAN_ORDER = {
    "Free": 0,
    "Basic": 1,
    "Pro": 2,
    "Enterprise": 3
}

PLANS = [
    "Free",
    "Basic",
    "Pro",
    "Enterprise"
]


# =========================================================
# 3. Load users.csv
# =========================================================

print("=" * 65)
print("SUBSCRIPTION DATA GENERATION")
print("=" * 65)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"users.csv not found at:\n{INPUT_FILE}"
    )

print("\nLoading users.csv...")

users = pd.read_csv(INPUT_FILE)

users["signup_date"] = pd.to_datetime(
    users["signup_date"],
    errors="coerce"
)


# =========================================================
# 4. Validate users.csv
# =========================================================

required_columns = [
    "user_id",
    "signup_date",
    "initial_plan",
    "account_status"
]

missing_columns = [
    col
    for col in required_columns
    if col not in users.columns
]

if missing_columns:
    raise ValueError(
        "Missing required columns:\n"
        + ", ".join(missing_columns)
    )

if users["user_id"].duplicated().any():
    raise ValueError(
        "Duplicate user_id found in users.csv."
    )

if users["signup_date"].isna().any():
    raise ValueError(
        "Missing or invalid signup_date found."
    )

if not users["initial_plan"].isin(PLANS).all():
    raise ValueError(
        "Unexpected plan found in initial_plan."
    )

print(
    f"Users loaded: {len(users):,}"
)


# =========================================================
# 5. Helper functions
# =========================================================

def choose_next_plan(current_plan: str) -> str:
    """
    Choose the next plan for an upgrade/downgrade event.
    """

    current_level = PLAN_ORDER[current_plan]

    # -----------------------------------------------------
    # Upgrade probability
    # -----------------------------------------------------

    if current_level == 0:  # Free

        return random.choices(
            ["Basic", "Pro"],
            weights=[0.85, 0.15],
            k=1
        )[0]

    elif current_level == 1:  # Basic

        return random.choices(
            ["Free", "Pro"],
            weights=[0.20, 0.80],
            k=1
        )[0]

    elif current_level == 2:  # Pro

        return random.choices(
            ["Basic", "Enterprise"],
            weights=[0.25, 0.75],
            k=1
        )[0]

    else:  # Enterprise

        return random.choices(
            ["Pro"],
            weights=[1.0],
            k=1
        )[0]


def random_end_date(
    start_date: pd.Timestamp,
    max_end_date: pd.Timestamp,
    min_months: int = 1,
    max_months: int = 12
) -> pd.Timestamp:
    """
    Generate a subscription end date between
    min_months and max_months after start date.
    """

    months = random.randint(
        min_months,
        max_months
    )

    end_date = (
        start_date
        + pd.DateOffset(months=months)
    )

    if end_date > max_end_date:
        end_date = max_end_date

    return pd.Timestamp(end_date)


# =========================================================
# 6. Generate subscriptions
# =========================================================

subscription_records = []

subscription_number = 1

print("\nGenerating subscription records...")


for user in users.itertuples(index=False):

    user_id = user.user_id
    signup_date = pd.Timestamp(user.signup_date)
    initial_plan = user.initial_plan
    account_status = user.account_status


    # -----------------------------------------------------
    # User cannot start subscription before signup
    # -----------------------------------------------------

    current_start_date = signup_date

    if current_start_date > END_DATE:
        continue


    # -----------------------------------------------------
    # Decide whether user should have multiple
    # subscription periods
    # -----------------------------------------------------

    if account_status == "Churned":
        max_subscription_records = random.choices(
            [1, 2, 3],
            weights=[0.65, 0.25, 0.10],
            k=1
        )[0]

    elif account_status == "Active":
        max_subscription_records = random.choices(
            [1, 2, 3, 4],
            weights=[0.35, 0.35, 0.20, 0.10],
            k=1
        )[0]

    elif account_status == "Inactive":
        max_subscription_records = random.choices(
            [1, 2],
            weights=[0.75, 0.25],
            k=1
        )[0]

    else:
        max_subscription_records = 1


    current_plan = initial_plan


    # -----------------------------------------------------
    # Generate subscription periods
    # -----------------------------------------------------

    for record_number in range(
        max_subscription_records
    ):

        if current_start_date > END_DATE:
            break


        # -------------------------------------------------
        # Determine subscription end date
        # -------------------------------------------------

        if record_number == max_subscription_records - 1:

            # Final subscription period
            if account_status == "Churned":

                end_date = random_end_date(
                    current_start_date,
                    END_DATE,
                    min_months=1,
                    max_months=12
                )

                subscription_status = "Cancelled"
                renewal_status = "Cancelled"

            elif account_status == "Inactive":

                end_date = random_end_date(
                    current_start_date,
                    END_DATE,
                    min_months=1,
                    max_months=8
                )

                subscription_status = "Expired"
                renewal_status = "Not Renewed"

            else:

                # Active subscription can continue
                # until the project end date
                end_date = random_end_date(
                    current_start_date,
                    END_DATE,
                    min_months=3,
                    max_months=12
                )

                if end_date >= END_DATE:

                    end_date = END_DATE
                    subscription_status = "Active"
                    renewal_status = "Pending"

                else:

                    subscription_status = "Active"
                    renewal_status = "Renewed"


        else:

            end_date = random_end_date(
                current_start_date,
                END_DATE,
                min_months=1,
                max_months=12
            )

            subscription_status = "Ended"
            renewal_status = "Renewed"


        # -------------------------------------------------
        # Monthly price
        # -------------------------------------------------

        monthly_price = PLAN_PRICES[current_plan]


        # -------------------------------------------------
        # Save record
        # -------------------------------------------------

        subscription_records.append({

            "subscription_id":
                f"SUB{subscription_number:08d}",

            "user_id":
                user_id,

            "plan_type":
                current_plan,

            "start_date":
                current_start_date.date(),

            "end_date":
                end_date.date(),

            "monthly_price":
                monthly_price,

            "subscription_status":
                subscription_status,

            "renewal_status":
                renewal_status
        })

        subscription_number += 1


        # -------------------------------------------------
        # Stop if we reached project end date
        # -------------------------------------------------

        if end_date >= END_DATE:
            break


        # -------------------------------------------------
        # Decide next plan
        # -------------------------------------------------

        # Free users are more likely to remain Free
        # before upgrading.
        if current_plan == "Free":

            upgrade_probability = 0.20

        elif current_plan == "Basic":

            upgrade_probability = 0.18

        elif current_plan == "Pro":

            upgrade_probability = 0.08

        else:

            upgrade_probability = 0.02


        should_change_plan = (
            random.random()
            < upgrade_probability
        )


        if should_change_plan:

            current_plan = choose_next_plan(
                current_plan
            )


        # -------------------------------------------------
        # Next subscription starts after previous one ends
        # -------------------------------------------------

        current_start_date = (
            end_date
            + pd.Timedelta(days=1)
        )


# =========================================================
# 7. Create DataFrame
# =========================================================

print("\nCreating DataFrame...")

subscriptions = pd.DataFrame(
    subscription_records
)

if subscriptions.empty:
    raise RuntimeError(
        "No subscription records were generated."
    )


# =========================================================
# 8. Convert data types
# =========================================================

subscriptions["start_date"] = pd.to_datetime(
    subscriptions["start_date"]
)

subscriptions["end_date"] = pd.to_datetime(
    subscriptions["end_date"]
)


# =========================================================
# 9. Validation
# =========================================================

print("Running validation checks...")


# Subscription IDs must be unique
assert subscriptions[
    "subscription_id"
].is_unique


# Every user must exist
assert subscriptions[
    "user_id"
].isin(
    users["user_id"]
).all()


# Start date cannot be after end date
assert (
    subscriptions["start_date"]
    <= subscriptions["end_date"]
).all()


# Subscription cannot start before signup
validation_df = subscriptions.merge(
    users[
        ["user_id", "signup_date"]
    ],
    on="user_id",
    how="left"
)

assert (
    validation_df["start_date"]
    >= validation_df["signup_date"]
).all()


# Dates must stay inside project range
assert (
    subscriptions["start_date"]
    >= START_DATE
).all()

assert (
    subscriptions["end_date"]
    <= END_DATE
).all()


# Monthly prices must match plan
price_check = subscriptions[
    "plan_type"
].map(PLAN_PRICES)

assert (
    subscriptions["monthly_price"]
    == price_check
).all()


# Valid plans
assert subscriptions[
    "plan_type"
].isin(PLANS).all()


# Non-negative monthly price
assert (
    subscriptions["monthly_price"]
    >= 0
).all()


# =========================================================
# 10. Sort records
# =========================================================

subscriptions = subscriptions.sort_values(
    by=[
        "user_id",
        "start_date"
    ]
).reset_index(drop=True)


# =========================================================
# 11. Save CSV
# =========================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

print("\nSaving subscriptions.csv...")

subscriptions.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# 12. Summary
# =========================================================

print("\n" + "=" * 65)
print("SUBSCRIPTIONS DATASET CREATED SUCCESSFULLY")
print("=" * 65)

print(
    f"Total users               : "
    f"{len(users):,}"
)

print(
    f"Total subscriptions       : "
    f"{len(subscriptions):,}"
)

print(
    f"Unique subscribed users   : "
    f"{subscriptions['user_id'].nunique():,}"
)

print(
    f"Average subscriptions/user: "
    f"{len(subscriptions) / subscriptions['user_id'].nunique():.2f}"
)

print(
    f"Total recurring MRR value : "
    f"${subscriptions['monthly_price'].sum():,.2f}"
)

print(
    f"Output file               : "
    f"{OUTPUT_FILE}"
)


# =========================================================
# 13. Plan summary
# =========================================================

print("\nSubscriptions by plan:")

plan_summary = (
    subscriptions
    .groupby("plan_type")
    .agg(
        subscriptions=(
            "subscription_id",
            "count"
        ),
        unique_users=(
            "user_id",
            "nunique"
        ),
        avg_monthly_price=(
            "monthly_price",
            "mean"
        )
    )
    .reset_index()
)

print(
    plan_summary.to_string(
        index=False
    )
)


# =========================================================
# 14. Status summary
# =========================================================

print("\nSubscriptions by status:")

status_summary = (
    subscriptions[
        "subscription_status"
    ]
    .value_counts()
)

print(status_summary)


# =========================================================
# 15. Renewal summary
# =========================================================

print("\nRenewal status:")

renewal_summary = (
    subscriptions[
        "renewal_status"
    ]
    .value_counts()
)

print(renewal_summary)


# =========================================================
# 16. Sample data
# =========================================================

print("\nSample records:")

print(
    subscriptions
    .head(10)
    .to_string(index=False)
)

print("\nGeneration completed.")