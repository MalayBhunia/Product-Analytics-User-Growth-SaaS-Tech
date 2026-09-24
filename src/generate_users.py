import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


# -----------------------------
# Configuration
# -----------------------------
N_USERS = 100_000
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2026, 8, 31)

OUTPUT_DIR = Path("../data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)
np.random.seed(42)


# -----------------------------
# Reference values
# -----------------------------
countries = [
    "India", "USA", "UK", "Canada", "Australia",
    "Germany", "Singapore", "UAE"
]

country_weights = [
    0.42, 0.18, 0.10, 0.07,
    0.06, 0.06, 0.05, 0.06
]

age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
age_weights = [0.18, 0.40, 0.25, 0.12, 0.05]

genders = ["Male", "Female", "Other"]
gender_weights = [0.62, 0.36, 0.02]

channels = [
    "Organic Search",
    "Google Ads",
    "Facebook Ads",
    "Instagram",
    "LinkedIn",
    "Email",
    "Referral"
]
channel_weights = [0.25, 0.20, 0.15, 0.12, 0.08, 0.10, 0.10]

devices = ["Mobile", "Desktop", "Tablet"]
device_weights = [0.42, 0.50, 0.08]

plans = ["Free", "Basic", "Pro", "Enterprise"]
plan_weights = [0.70, 0.20, 0.08, 0.02]

statuses = ["Active", "Inactive", "Churned"]
status_weights = [0.72, 0.18, 0.10]


# -----------------------------
# Generate signup dates
# -----------------------------
date_range_days = (END_DATE - START_DATE).days

signup_dates = [
    START_DATE + timedelta(days=random.randint(0, date_range_days))
    for _ in range(N_USERS)
]


# -----------------------------
# Create dataset
# -----------------------------
df = pd.DataFrame({
    "user_id": np.arange(100001, 100001 + N_USERS),

    "signup_date": signup_dates,

    "country": np.random.choice(
        countries,
        size=N_USERS,
        p=country_weights
    ),

    "age_group": np.random.choice(
        age_groups,
        size=N_USERS,
        p=age_weights
    ),

    "gender": np.random.choice(
        genders,
        size=N_USERS,
        p=gender_weights
    ),

    "acquisition_channel": np.random.choice(
        channels,
        size=N_USERS,
        p=channel_weights
    ),

    "device_type": np.random.choice(
        devices,
        size=N_USERS,
        p=device_weights
    ),

    "initial_plan": np.random.choice(
        plans,
        size=N_USERS,
        p=plan_weights
    ),

    "account_status": np.random.choice(
        statuses,
        size=N_USERS,
        p=status_weights
    )
})


# -----------------------------
# Data validation
# -----------------------------
df["signup_date"] = pd.to_datetime(df["signup_date"])

assert df["user_id"].is_unique
assert df["user_id"].notna().all()
assert df["signup_date"].between(
    START_DATE,
    END_DATE
).all()


# -----------------------------
# Save CSV
# -----------------------------
output_file = OUTPUT_DIR / "users.csv"

df.to_csv(
    output_file,
    index=False
)

print("Users generated successfully!")
print(f"Rows: {len(df):,}")
print(f"File: {output_file}")
print("\nSample:")
print(df.head())