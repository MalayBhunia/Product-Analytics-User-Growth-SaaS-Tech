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
OUTPUT_FILE = OUTPUT_DIR / "sessions.csv"

END_DATE = pd.Timestamp("2026-08-31")

random.seed(42)
np.random.seed(42)


# =========================================================
# 2. Load users.csv
# =========================================================

print("Loading users.csv...")

users = pd.read_csv(INPUT_FILE)

users["signup_date"] = pd.to_datetime(users["signup_date"])

print(f"Users loaded: {len(users):,}")


# =========================================================
# 3. Validate input
# =========================================================

required_columns = [
    "user_id",
    "signup_date",
    "device_type",
    "account_status"
]

missing_columns = [
    col for col in required_columns
    if col not in users.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns in users.csv: {missing_columns}"
    )

if not users["user_id"].is_unique:
    raise ValueError("user_id contains duplicates.")

if users["signup_date"].isna().any():
    raise ValueError("signup_date contains missing values.")


# =========================================================
# 4. Generate sessions
# =========================================================

print("Generating sessions...")

session_records = []

session_id = 1


for row in users.itertuples(index=False):

    user_id = row.user_id
    signup_date = row.signup_date
    account_status = row.account_status
    device_type = row.device_type

    # -----------------------------------------------------
    # User lifetime
    # -----------------------------------------------------

    lifetime_days = (END_DATE - signup_date).days

    if lifetime_days < 0:
        continue

    lifetime_months = max(
        0.5,
        lifetime_days / 30
    )


    # -----------------------------------------------------
    # Average sessions per month
    #
    # These values are intentionally moderate so that
    # the final dataset stays around 4–6M sessions.
    # -----------------------------------------------------

    if account_status == "Active":
        sessions_per_month = 3.0

    elif account_status == "Inactive":
        sessions_per_month = 1.0

    elif account_status == "Churned":
        sessions_per_month = 1.5

    else:
        sessions_per_month = 1.5


    # -----------------------------------------------------
    # User-level activity variation
    #
    # Some users are highly engaged,
    # some users are light users.
    # -----------------------------------------------------

    activity_factor = np.random.lognormal(
        mean=0,
        sigma=0.35
    )

    expected_sessions = (
        lifetime_months
        * sessions_per_month
        * activity_factor
    )


    # -----------------------------------------------------
    # Generate number of sessions
    # -----------------------------------------------------

    n_sessions = np.random.poisson(
        max(1, expected_sessions)
    )

    n_sessions = max(
        1,
        n_sessions
    )


    # -----------------------------------------------------
    # Generate each session
    # -----------------------------------------------------

    for _ in range(n_sessions):

        # -----------------------------------------------
        # Session date
        # -----------------------------------------------

        if lifetime_days == 0:

            session_date = signup_date

        else:

            days_after_signup = random.randint(
                0,
                lifetime_days
            )

            session_date = (
                signup_date
                + pd.Timedelta(
                    days=days_after_signup
                )
            )


        # -----------------------------------------------
        # Session time
        # -----------------------------------------------

        hour = random.choices(
            population=list(range(6, 24)),
            weights=[
                1, 1, 2, 3, 4, 5,
                6, 7, 8, 9, 10, 9,
                8, 8, 9, 10, 8, 6
            ],
            k=1
        )[0]

        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        session_start = (
            pd.Timestamp(session_date)
            + pd.Timedelta(
                hours=hour,
                minutes=minute,
                seconds=second
            )
        )


        # -----------------------------------------------
        # Session duration
        # -----------------------------------------------

        if account_status == "Active":

            duration = np.random.gamma(
                shape=2.2,
                scale=8
            )

        elif account_status == "Inactive":

            duration = np.random.gamma(
                shape=1.7,
                scale=6
            )

        elif account_status == "Churned":

            duration = np.random.gamma(
                shape=1.8,
                scale=6
            )

        else:

            duration = np.random.gamma(
                shape=2.0,
                scale=7
            )


        session_duration = int(
            max(
                1,
                min(duration, 120)
            )
        )


        # -----------------------------------------------
        # Pages viewed
        # -----------------------------------------------

        expected_pages = max(
            1,
            session_duration / 5
        )

        pages_viewed = int(
            np.random.poisson(
                expected_pages
            )
        )

        pages_viewed = max(
            1,
            min(pages_viewed, 40)
        )


        # -----------------------------------------------
        # Store session
        # -----------------------------------------------

        session_records.append({

            "session_id":
                f"S{session_id:09d}",

            "user_id":
                user_id,

            "session_date":
                session_start.date(),

            "session_start":
                session_start.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "session_duration_minutes":
                session_duration,

            "pages_viewed":
                pages_viewed,

            "device_type":
                device_type
        })

        session_id += 1


# =========================================================
# 5. Create DataFrame
# =========================================================

print("Creating DataFrame...")

sessions = pd.DataFrame(
    session_records
)


# =========================================================
# 6. Validation
# =========================================================

if sessions.empty:
    raise ValueError(
        "No sessions were generated."
    )

# Unique session IDs
assert sessions["session_id"].is_unique


# Valid users
assert sessions["user_id"].isin(
    users["user_id"]
).all()


# Convert dates
sessions["session_date"] = pd.to_datetime(
    sessions["session_date"]
)

validation_df = sessions.merge(
    users[
        ["user_id", "signup_date"]
    ],
    on="user_id",
    how="left"
)


# Session cannot happen before signup
if not (
    validation_df["session_date"]
    >= validation_df["signup_date"]
).all():

    raise ValueError(
        "Some sessions occur before user signup."
    )


# Session cannot exceed project end date
if not (
    validation_df["session_date"]
    <= END_DATE
).all():

    raise ValueError(
        "Some sessions occur after END_DATE."
    )


# Duration validation
if not (
    sessions["session_duration_minutes"]
    > 0
).all():

    raise ValueError(
        "Invalid session duration found."
    )


# Pages validation
if not (
    sessions["pages_viewed"]
    > 0
).all():

    raise ValueError(
        "Invalid pages_viewed found."
    )


# =========================================================
# 7. Save CSV
# =========================================================

print("Saving sessions.csv...")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

sessions.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# 8. Summary
# =========================================================

print("\n" + "=" * 55)
print("SESSION DATASET GENERATED SUCCESSFULLY")
print("=" * 55)

print(
    f"Total users           : {len(users):,}"
)

print(
    f"Total sessions        : {len(sessions):,}"
)

print(
    f"Unique users          : "
    f"{sessions['user_id'].nunique():,}"
)

print(
    f"Average sessions/user : "
    f"{len(sessions) / len(users):.2f}"
)

print(
    f"Average duration      : "
    f"{sessions['session_duration_minutes'].mean():.2f} min"
)

print(
    f"Average pages/session : "
    f"{sessions['pages_viewed'].mean():.2f}"
)

print(
    f"Output file           : {OUTPUT_FILE}"
)


# =========================================================
# 9. Status summary
# =========================================================

status_summary = (
    sessions
    .merge(
        users[
            ["user_id", "account_status"]
        ],
        on="user_id",
        how="left"
    )
    .groupby("account_status")
    .agg(
        total_sessions=(
            "session_id",
            "count"
        ),
        unique_users=(
            "user_id",
            "nunique"
        ),
        avg_duration=(
            "session_duration_minutes",
            "mean"
        )
    )
    .reset_index()
)

print("\nSessions by account status:")
print(
    status_summary.to_string(
        index=False
    )
)


# =========================================================
# 10. Sample
# =========================================================

print("\nSample data:")
print(
    sessions.head(10).to_string(
        index=False
    )
)