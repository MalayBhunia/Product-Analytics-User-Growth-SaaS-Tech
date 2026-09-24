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
OUTPUT_FILE = OUTPUT_DIR / "marketing_campaigns.csv"

START_DATE = pd.Timestamp("2022-01-01")
END_DATE = pd.Timestamp("2026-08-31")

random.seed(42)
np.random.seed(42)


# =========================================================
# 2. Marketing channels
# =========================================================

CHANNELS = [
    "Organic Search",
    "Google Ads",
    "Facebook Ads",
    "Instagram",
    "LinkedIn",
    "Email",
    "Referral"
]


# =========================================================
# 3. Campaign configuration
# =========================================================

CAMPAIGNS = {
    "Organic Search": [
        "SEO_Brand",
        "SEO_Product",
        "SEO_Content"
    ],

    "Google Ads": [
        "Google_Search",
        "Google_Display",
        "Google_Remarketing"
    ],

    "Facebook Ads": [
        "Facebook_Conversion",
        "Facebook_LeadGen",
        "Facebook_Retargeting"
    ],

    "Instagram": [
        "Instagram_Reels",
        "Instagram_Stories",
        "Instagram_Influencer"
    ],

    "LinkedIn": [
        "LinkedIn_B2B",
        "LinkedIn_LeadGen",
        "LinkedIn_SaaS"
    ],

    "Email": [
        "Email_Welcome",
        "Email_ProductUpdate",
        "Email_Promotion"
    ],

    "Referral": [
        "Referral_Program",
        "Referral_Invite",
        "Referral_Partner"
    ]
}


# =========================================================
# 4. Channel performance configuration
# =========================================================

# Typical click-through-rate ranges
CTR_RANGE = {

    "Organic Search": (0.04, 0.10),

    "Google Ads": (0.03, 0.08),

    "Facebook Ads": (0.015, 0.045),

    "Instagram": (0.015, 0.040),

    "LinkedIn": (0.015, 0.050),

    "Email": (0.08, 0.25),

    "Referral": (0.10, 0.30)
}


# Conversion rate after click
CONVERSION_RANGE = {

    "Organic Search": (0.06, 0.15),

    "Google Ads": (0.04, 0.10),

    "Facebook Ads": (0.025, 0.07),

    "Instagram": (0.025, 0.07),

    "LinkedIn": (0.06, 0.14),

    "Email": (0.08, 0.20),

    "Referral": (0.10, 0.25)
}


# Approximate cost per click
CPC_RANGE = {

    "Organic Search": (0.10, 0.80),

    "Google Ads": (0.80, 2.50),

    "Facebook Ads": (0.30, 1.20),

    "Instagram": (0.25, 1.00),

    "LinkedIn": (1.50, 4.00),

    "Email": (0.05, 0.30),

    "Referral": (0.10, 0.80)
}


# =========================================================
# 5. Load users.csv
# =========================================================

print("=" * 65)
print("MARKETING CAMPAIGN DATA GENERATION")
print("=" * 65)

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"users.csv not found at:\n{INPUT_FILE}"
    )


print("\nLoading users.csv...")

users = pd.read_csv(
    INPUT_FILE
)

users["signup_date"] = pd.to_datetime(
    users["signup_date"],
    errors="coerce"
)


# =========================================================
# 6. Validate users.csv
# =========================================================

required_columns = [
    "user_id",
    "signup_date",
    "acquisition_channel"
]

missing_columns = [
    column
    for column in required_columns
    if column not in users.columns
]

if missing_columns:

    raise ValueError(
        "Missing required columns:\n"
        + ", ".join(missing_columns)
    )


if users["user_id"].duplicated().any():

    raise ValueError(
        "Duplicate user_id found."
    )


if users["signup_date"].isna().any():

    raise ValueError(
        "Invalid signup_date found."
    )


if not users[
    "acquisition_channel"
].isin(CHANNELS).all():

    raise ValueError(
        "Invalid acquisition channel found."
    )


print(
    f"Users loaded: {len(users):,}"
)


# =========================================================
# 7. Generate marketing records
# =========================================================

print("\nGenerating marketing records...")

marketing_records = []

campaign_number = 1


for user in users.itertuples(
    index=False
):

    user_id = user.user_id
    signup_date = pd.Timestamp(
        user.signup_date
    )
    acquisition_channel = (
        user.acquisition_channel
    )


    # -----------------------------------------------------
    # Marketing record date
    # -----------------------------------------------------

    # Campaign interaction occurs before or around signup.
    # To keep the logic simple and realistic,
    # most records will occur within 30 days before signup.

    days_before_signup = random.randint(
        0,
        30
    )

    campaign_date = (
        signup_date
        - pd.Timedelta(
            days=days_before_signup
        )
    )


    # Do not allow date before project start
    if campaign_date < START_DATE:

        campaign_date = START_DATE


    # -----------------------------------------------------
    # Campaign name
    # -----------------------------------------------------

    campaign_name = random.choice(
        CAMPAIGNS[
            acquisition_channel
        ]
    )


    # -----------------------------------------------------
    # Impressions
    # -----------------------------------------------------

    if acquisition_channel == "Email":

        impressions = random.randint(
            200,
            5000
        )

    elif acquisition_channel == "Referral":

        impressions = random.randint(
            50,
            1500
        )

    else:

        impressions = random.randint(
            500,
            20000
        )


    # -----------------------------------------------------
    # Click-through rate
    # -----------------------------------------------------

    ctr = random.uniform(
        *CTR_RANGE[
            acquisition_channel
        ]
    )


    clicks = int(
        impressions * ctr
    )

    clicks = max(
        1,
        clicks
    )


    # -----------------------------------------------------
    # Conversion rate
    # -----------------------------------------------------

    conversion_rate = random.uniform(
        *CONVERSION_RANGE[
            acquisition_channel
        ]
    )


    conversions = int(
        clicks * conversion_rate
    )


    # Make sure acquisition user converts
    # in their own acquisition record.
    if conversions == 0:

        conversions = 1


    # -----------------------------------------------------
    # Cost
    # -----------------------------------------------------

    cpc = random.uniform(
        *CPC_RANGE[
            acquisition_channel
        ]
    )


    spend = clicks * cpc


    # Organic, Email and Referral are cheaper
    if acquisition_channel == "Organic Search":

        spend *= random.uniform(
            0.15,
            0.40
        )

    elif acquisition_channel == "Email":

        spend *= random.uniform(
            0.10,
            0.35
        )

    elif acquisition_channel == "Referral":

        spend *= random.uniform(
            0.20,
            0.60
        )


    spend = round(
        max(0, spend),
        2
    )


    # -----------------------------------------------------
    # Save record
    # -----------------------------------------------------

    marketing_records.append({

        "campaign_id":
            f"CAMP{campaign_number:08d}",

        "user_id":
            user_id,

        "campaign_date":
            campaign_date.date(),

        "campaign_name":
            campaign_name,

        "channel":
            acquisition_channel,

        "impressions":
            impressions,

        "clicks":
            clicks,

        "spend":
            spend,

        "conversion":
            conversions
    })


    campaign_number += 1


# =========================================================
# 8. Create DataFrame
# =========================================================

marketing = pd.DataFrame(
    marketing_records
)


if marketing.empty:

    raise RuntimeError(
        "No marketing records were generated."
    )


marketing["campaign_date"] = pd.to_datetime(
    marketing["campaign_date"]
)


# =========================================================
# 9. Validation
# =========================================================

print("\nRunning validation checks...")


# Campaign ID unique
assert marketing[
    "campaign_id"
].is_unique


# Every user exists
assert marketing[
    "user_id"
].isin(
    users["user_id"]
).all()


# Valid channels
assert marketing[
    "channel"
].isin(CHANNELS).all()


# Positive impressions
assert (
    marketing["impressions"]
    > 0
).all()


# Clicks cannot exceed impressions
assert (
    marketing["clicks"]
    <= marketing["impressions"]
).all()


# Positive / non-negative conversions
assert (
    marketing["conversion"]
    >= 0
).all()


# Conversions cannot exceed clicks
assert (
    marketing["conversion"]
    <= marketing["clicks"]
).all()


# Non-negative spend
assert (
    marketing["spend"]
    >= 0
).all()


# Campaign date should not be after signup
validation_df = marketing.merge(
    users[
        [
            "user_id",
            "signup_date",
            "acquisition_channel"
        ]
    ],
    on="user_id",
    how="left"
)


if not (
    validation_df["campaign_date"]
    <= validation_df["signup_date"]
).all():

    raise ValueError(
        "Campaign date occurs after signup."
    )


# User acquisition channel must match
if not (
    validation_df["channel"]
    == validation_df[
        "acquisition_channel"
    ]
).all():

    raise ValueError(
        "Marketing channel does not match "
        "user acquisition channel."
    )


# Project date range
assert (
    marketing["campaign_date"]
    >= START_DATE
).all()

assert (
    marketing["campaign_date"]
    <= END_DATE
).all()


# =========================================================
# 10. Save CSV
# =========================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

if OUTPUT_FILE.exists():

    OUTPUT_FILE.unlink()

print("\nSaving marketing_campaigns.csv...")

marketing.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# 11. Final summary
# =========================================================

print("\n" + "=" * 65)
print("MARKETING DATASET CREATED SUCCESSFULLY")
print("=" * 65)

print(
    f"Total users            : "
    f"{len(users):,}"
)

print(
    f"Marketing records      : "
    f"{len(marketing):,}"
)

print(
    f"Unique users           : "
    f"{marketing['user_id'].nunique():,}"
)

print(
    f"Total impressions      : "
    f"{marketing['impressions'].sum():,}"
)

print(
    f"Total clicks           : "
    f"{marketing['clicks'].sum():,}"
)

print(
    f"Total conversions      : "
    f"{marketing['conversion'].sum():,}"
)

print(
    f"Total marketing spend  : "
    f"${marketing['spend'].sum():,.2f}"
)

print(
    f"Output file            : "
    f"{OUTPUT_FILE}"
)


# =========================================================
# 12. Channel summary
# =========================================================

print("\nMarketing performance by channel:")

channel_summary = (
    marketing
    .groupby("channel")
    .agg(
        users=(
            "user_id",
            "nunique"
        ),

        impressions=(
            "impressions",
            "sum"
        ),

        clicks=(
            "clicks",
            "sum"
        ),

        conversions=(
            "conversion",
            "sum"
        ),

        spend=(
            "spend",
            "sum"
        )
    )
    .reset_index()
)


channel_summary["ctr"] = (
    channel_summary["clicks"]
    / channel_summary["impressions"]
)

channel_summary["conversion_rate"] = (
    channel_summary["conversions"]
    / channel_summary["clicks"]
)

channel_summary["cpa"] = np.where(
    channel_summary["conversions"] > 0,
    channel_summary["spend"]
    / channel_summary["conversions"],
    0
)


print(
    channel_summary.to_string(
        index=False
    )
)


# =========================================================
# 13. Sample
# =========================================================

print("\nSample records:")

print(
    marketing
    .head(10)
    .to_string(index=False)
)


print("\nGeneration completed successfully.")