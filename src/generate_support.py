# generate_support_tickets.py

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
OUTPUT_FILE = OUTPUT_DIR / "support_tickets.csv"

START_DATE = pd.Timestamp("2022-01-01")
END_DATE = pd.Timestamp("2026-08-31")

random.seed(42)
np.random.seed(42)


# =========================================================
# 2. Ticket configuration
# =========================================================

TICKET_CATEGORIES = [
    "Technical Issue",
    "Billing",
    "Login / Access",
    "Feature Request",
    "Performance",
    "Account Issue",
    "Integration"
]

CATEGORY_WEIGHTS = [
    0.28,
    0.15,
    0.18,
    0.10,
    0.12,
    0.09,
    0.08
]


PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Urgent"
]

PRIORITY_WEIGHTS = [
    0.30,
    0.45,
    0.20,
    0.05
]


TICKET_STATUSES = [
    "Resolved",
    "Closed",
    "Open",
    "Pending"
]

STATUS_WEIGHTS = [
    0.55,
    0.25,
    0.10,
    0.10
]


# =========================================================
# 3. Load users.csv
# =========================================================

print("=" * 65)
print("SUPPORT TICKET DATA GENERATION")
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
        "Invalid signup_date found."
    )


print(
    f"Users loaded: {len(users):,}"
)


# =========================================================
# 5. Generate support tickets
# =========================================================

print("\nGenerating support tickets...")

ticket_records = []

ticket_number = 1


for user in users.itertuples(index=False):

    user_id = user.user_id
    signup_date = pd.Timestamp(
        user.signup_date
    )
    account_status = user.account_status


    # -----------------------------------------------------
    # Determine expected tickets per user
    # -----------------------------------------------------

    if account_status == "Active":

        expected_tickets = 0.25

    elif account_status == "Inactive":

        expected_tickets = 0.35

    elif account_status == "Churned":

        expected_tickets = 0.55

    else:

        expected_tickets = 0.30


    # -----------------------------------------------------
    # Add user-level variation
    # -----------------------------------------------------

    support_factor = np.random.lognormal(
        mean=0,
        sigma=0.60
    )

    expected_tickets *= support_factor


    # -----------------------------------------------------
    # Number of tickets
    # -----------------------------------------------------

    n_tickets = np.random.poisson(
        expected_tickets
    )

    # Most users may have no tickets.
    # Some users may have multiple tickets.
    n_tickets = min(
        n_tickets,
        5
    )


    # -----------------------------------------------------
    # Generate ticket records
    # -----------------------------------------------------

    for _ in range(n_tickets):

        # ---------------------------------------------
        # Ticket date
        # ---------------------------------------------

        available_days = (
            END_DATE - signup_date
        ).days

        if available_days < 0:
            continue

        if available_days == 0:

            created_date = signup_date

        else:

            days_after_signup = random.randint(
                0,
                available_days
            )

            created_date = (
                signup_date
                + pd.Timedelta(
                    days=days_after_signup
                )
            )


        # ---------------------------------------------
        # Category
        # ---------------------------------------------

        category = np.random.choice(
            TICKET_CATEGORIES,
            p=CATEGORY_WEIGHTS
        )


        # ---------------------------------------------
        # Priority
        # ---------------------------------------------

        priority = np.random.choice(
            PRIORITIES,
            p=PRIORITY_WEIGHTS
        )


        # ---------------------------------------------
        # Ticket status
        # ---------------------------------------------

        ticket_status = np.random.choice(
            TICKET_STATUSES,
            p=STATUS_WEIGHTS
        )


        # ---------------------------------------------
        # Resolution time
        # ---------------------------------------------

        if priority == "Urgent":

            resolution_time = np.random.gamma(
                shape=2.0,
                scale=4.0
            )

        elif priority == "High":

            resolution_time = np.random.gamma(
                shape=2.0,
                scale=6.0
            )

        elif priority == "Medium":

            resolution_time = np.random.gamma(
                shape=2.0,
                scale=10.0
            )

        else:

            resolution_time = np.random.gamma(
                shape=2.0,
                scale=18.0
            )


        resolution_time = round(
            max(
                0.5,
                min(
                    resolution_time,
                    168
                )
            ),
            2
        )


        # ---------------------------------------------
        # Customer rating
        # ---------------------------------------------

        if ticket_status in [
            "Open",
            "Pending"
        ]:

            customer_rating = np.nan

        else:

            # Higher resolution time may slightly
            # reduce customer satisfaction.

            base_rating = 4.5

            rating_penalty = min(
                2.5,
                resolution_time / 40
            )

            rating = (
                base_rating
                - rating_penalty
                + np.random.normal(
                    0,
                    0.35
                )
            )

            customer_rating = round(
                max(
                    1,
                    min(
                        5,
                        rating
                    )
                ),
                1
            )


        # ---------------------------------------------
        # Save record
        # ---------------------------------------------

        ticket_records.append({

            "ticket_id":
                f"TKT{ticket_number:08d}",

            "user_id":
                user_id,

            "created_date":
                created_date.date(),

            "category":
                category,

            "priority":
                priority,

            "resolution_time_hours":
                resolution_time,

            "ticket_status":
                ticket_status,

            "customer_rating":
                customer_rating
        })


        ticket_number += 1


# =========================================================
# 6. Create DataFrame
# =========================================================

print("\nCreating DataFrame...")

tickets = pd.DataFrame(
    ticket_records
)


if tickets.empty:

    raise RuntimeError(
        "No support tickets were generated."
    )


# =========================================================
# 7. Convert date
# =========================================================

tickets["created_date"] = pd.to_datetime(
    tickets["created_date"]
)


# =========================================================
# 8. Validation
# =========================================================

print("Running validation checks...")


# Ticket ID unique
assert tickets[
    "ticket_id"
].is_unique


# Every user must exist
assert tickets[
    "user_id"
].isin(
    users["user_id"]
).all()


# Valid ticket categories
assert tickets[
    "category"
].isin(
    TICKET_CATEGORIES
).all()


# Valid priorities
assert tickets[
    "priority"
].isin(
    PRIORITIES
).all()


# Valid statuses
assert tickets[
    "ticket_status"
].isin(
    TICKET_STATUSES
).all()


# Positive resolution time
assert (
    tickets[
        "resolution_time_hours"
    ] > 0
).all()


# Ticket date must be after signup
validation_df = tickets.merge(
    users[
        [
            "user_id",
            "signup_date"
        ]
    ],
    on="user_id",
    how="left"
)


if not (
    validation_df["created_date"]
    >= validation_df["signup_date"]
).all():

    raise ValueError(
        "Some tickets were created before signup."
    )


# Ticket date must be within project period
assert (
    tickets["created_date"]
    >= START_DATE
).all()


assert (
    tickets["created_date"]
    <= END_DATE
).all()


# Customer rating validation
rated_tickets = tickets[
    tickets["customer_rating"].notna()
]

if not rated_tickets.empty:

    assert (
        rated_tickets["customer_rating"]
        >= 1
    ).all()

    assert (
        rated_tickets["customer_rating"]
        <= 5
    ).all()


# =========================================================
# 9. Save CSV
# =========================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

if OUTPUT_FILE.exists():

    OUTPUT_FILE.unlink()

print("\nSaving support_tickets.csv...")

tickets.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# 10. Final summary
# =========================================================

print("\n" + "=" * 65)
print("SUPPORT TICKETS DATASET CREATED SUCCESSFULLY")
print("=" * 65)

print(
    f"Total users          : "
    f"{len(users):,}"
)

print(
    f"Total tickets        : "
    f"{len(tickets):,}"
)

print(
    f"Unique users         : "
    f"{tickets['user_id'].nunique():,}"
)

print(
    f"Avg tickets/user     : "
    f"{len(tickets) / len(tickets['user_id'].unique()):.2f}"
)

print(
    f"Avg resolution time  : "
    f"{tickets['resolution_time_hours'].mean():.2f} hours"
)

print(
    f"Output file          : "
    f"{OUTPUT_FILE}"
)


# =========================================================
# 11. Category summary
# =========================================================

print("\nTickets by category:")

category_summary = (
    tickets[
        "category"
    ]
    .value_counts()
)

print(
    category_summary.to_string()
)


# =========================================================
# 12. Priority summary
# =========================================================

print("\nTickets by priority:")

priority_summary = (
    tickets[
        "priority"
    ]
    .value_counts()
)

print(
    priority_summary.to_string()
)


# =========================================================
# 13. Status summary
# =========================================================

print("\nTickets by status:")

status_summary = (
    tickets[
        "ticket_status"
    ]
    .value_counts()
)

print(
    status_summary.to_string()
)


# =========================================================
# 14. Account status comparison
# =========================================================

print("\nSupport activity by account status:")

support_status_summary = (
    tickets
    .merge(
        users[
            [
                "user_id",
                "account_status"
            ]
        ],
        on="user_id",
        how="left"
    )
    .groupby("account_status")
    .agg(
        tickets=(
            "ticket_id",
            "count"
        ),
        unique_users=(
            "user_id",
            "nunique"
        ),
        avg_resolution_hours=(
            "resolution_time_hours",
            "mean"
        ),
        avg_rating=(
            "customer_rating",
            "mean"
        )
    )
    .reset_index()
)

print(
    support_status_summary.to_string(
        index=False
    )
)


# =========================================================
# 15. Sample data
# =========================================================

print("\nSample records:")

print(
    tickets
    .head(10)
    .to_string(index=False)
)


print("\nGeneration completed successfully.")