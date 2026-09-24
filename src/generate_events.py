import random
from pathlib import Path

import numpy as np
import pandas as pd


# =========================================================
# 1. Configuration
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "sessions.csv"
OUTPUT_DIR = BASE_DIR / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "product_events.csv"

END_DATE = pd.Timestamp("2026-08-31")

CHUNK_SIZE = 100_000

# IMPORTANT:
# Product events will NEVER exceed this number.
MAX_EVENTS = 20_000_000

random.seed(42)
np.random.seed(42)


# =========================================================
# 2. Event definitions
# =========================================================

EVENT_FEATURE_MAP = {
    "login": "Authentication",
    "dashboard_view": "Dashboard",
    "project_created": "Project Management",
    "file_uploaded": "File Management",
    "report_generated": "Reporting",
    "report_downloaded": "Reporting",
    "team_invited": "Collaboration",
    "integration_connected": "Integrations",
    "settings_updated": "Account Settings",
    "search_performed": "Search",
    "notification_viewed": "Notifications"
}


# =========================================================
# 3. Event generation function
# =========================================================

def choose_events(
    session_duration: int,
    pages_viewed: int
) -> list[str]:
    """
    Generate 1–4 realistic product events
    depending on session engagement.

    Average is intentionally kept low so that
    total events remain within the target range.
    """

    # -----------------------------------------------------
    # Low engagement session
    # -----------------------------------------------------

    if session_duration <= 5 or pages_viewed <= 2:

        event_count = random.choices(
            [1, 2],
            weights=[0.70, 0.30],
            k=1
        )[0]

        extra_events = [
            "notification_viewed",
            "search_performed"
        ]

        selected = ["login"]

        if event_count == 2:
            selected.append(
                random.choice(extra_events)
            )

        return selected


    # -----------------------------------------------------
    # Medium engagement session
    # -----------------------------------------------------

    elif session_duration <= 20 or pages_viewed <= 5:

        event_count = random.choices(
            [2, 3],
            weights=[0.65, 0.35],
            k=1
        )[0]

        selected = [
            "login",
            "dashboard_view"
        ]

        additional_events = [
            "project_created",
            "file_uploaded",
            "report_generated",
            "search_performed",
            "notification_viewed"
        ]

        additional_count = event_count - 2

        for _ in range(additional_count):
            selected.append(
                random.choice(additional_events)
            )

        return selected


    # -----------------------------------------------------
    # High engagement session
    # -----------------------------------------------------

    else:

        event_count = random.choices(
            [3, 4],
            weights=[0.75, 0.25],
            k=1
        )[0]

        selected = [
            "login",
            "dashboard_view"
        ]

        additional_events = [
            "project_created",
            "file_uploaded",
            "report_generated",
            "report_downloaded",
            "team_invited",
            "integration_connected",
            "search_performed"
        ]

        additional_count = event_count - 2

        for _ in range(additional_count):
            selected.append(
                random.choice(additional_events)
            )

        return selected


# =========================================================
# 4. Validate input
# =========================================================

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"\nsessions.csv was not found at:\n{INPUT_FILE}"
    )


print("=" * 65)
print("PRODUCT EVENTS GENERATION")
print("=" * 65)

print(f"Input file  : {INPUT_FILE}")
print(f"Output file : {OUTPUT_FILE}")
print(f"Chunk size  : {CHUNK_SIZE:,}")
print(f"Max events  : {MAX_EVENTS:,}")


# =========================================================
# 5. Check required columns
# =========================================================

required_columns = [
    "session_id",
    "user_id",
    "session_date",
    "session_start",
    "session_duration_minutes",
    "pages_viewed",
    "device_type"
]

header = pd.read_csv(
    INPUT_FILE,
    nrows=0
)

missing_columns = [
    col
    for col in required_columns
    if col not in header.columns
]

if missing_columns:

    raise ValueError(
        "\nMissing columns in sessions.csv:\n"
        + ", ".join(missing_columns)
    )


# =========================================================
# 6. Remove previous output
# =========================================================

if OUTPUT_FILE.exists():

    OUTPUT_FILE.unlink()

    print("\nOld product_events.csv deleted.")


# =========================================================
# 7. Counters
# =========================================================

total_sessions_processed = 0
total_events_generated = 0

chunk_number = 0

first_chunk = True


# =========================================================
# 8. Process sessions chunk-by-chunk
# =========================================================

for sessions_chunk in pd.read_csv(
    INPUT_FILE,
    chunksize=CHUNK_SIZE
):

    chunk_number += 1

    print(
        f"\nProcessing chunk {chunk_number}..."
    )


    # -----------------------------------------------------
    # Convert columns
    # -----------------------------------------------------

    sessions_chunk["session_date"] = pd.to_datetime(
        sessions_chunk["session_date"],
        errors="coerce"
    )

    sessions_chunk["session_start"] = pd.to_datetime(
        sessions_chunk["session_start"],
        errors="coerce"
    )


    # -----------------------------------------------------
    # Validate data
    # -----------------------------------------------------

    if sessions_chunk["session_date"].isna().any():

        raise ValueError(
            f"Invalid session_date in chunk "
            f"{chunk_number}"
        )


    if sessions_chunk["session_start"].isna().any():

        raise ValueError(
            f"Invalid session_start in chunk "
            f"{chunk_number}"
        )


    if (
        sessions_chunk["session_duration_minutes"]
        <= 0
    ).any():

        raise ValueError(
            f"Invalid session duration in chunk "
            f"{chunk_number}"
        )


    if (
        sessions_chunk["pages_viewed"]
        <= 0
    ).any():

        raise ValueError(
            f"Invalid pages_viewed in chunk "
            f"{chunk_number}"
        )


    # -----------------------------------------------------
    # Generate event records
    # -----------------------------------------------------

    event_records = []


    for session in sessions_chunk.itertuples(
        index=False
    ):

        # Stop completely if hard limit reached
        if total_events_generated >= MAX_EVENTS:
            break


        session_id = session.session_id
        user_id = session.user_id
        session_start = session.session_start

        duration = int(
            session.session_duration_minutes
        )

        pages_viewed = int(
            session.pages_viewed
        )

        device_type = session.device_type


        # -------------------------------------------------
        # Get event types
        # -------------------------------------------------

        events = choose_events(
            session_duration=duration,
            pages_viewed=pages_viewed
        )


        # -------------------------------------------------
        # Create event records
        # -------------------------------------------------

        for event_name in events:

            # ---------------------------------------------
            # Hard maximum
            # ---------------------------------------------

            if (
                total_events_generated
                + len(event_records)
                >= MAX_EVENTS
            ):
                break


            # ---------------------------------------------
            # Generate timestamp
            # ---------------------------------------------

            max_seconds = max(
                1,
                duration * 60
            )

            event_offset = random.randint(
                0,
                max_seconds
            )

            event_timestamp = (
                session_start
                + pd.Timedelta(
                    seconds=event_offset
                )
            )


            # ---------------------------------------------
            # Keep event within project timeline
            # ---------------------------------------------

            max_datetime = (
                END_DATE
                + pd.Timedelta(
                    hours=23,
                    minutes=59,
                    seconds=59
                )
            )

            if event_timestamp > max_datetime:

                event_timestamp = max_datetime


            # ---------------------------------------------
            # Store record
            # ---------------------------------------------

            event_records.append({

                "user_id": user_id,

                "session_id": session_id,

                "event_date":
                    event_timestamp.date(),

                "event_timestamp":
                    event_timestamp.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "event_name":
                    event_name,

                "feature_name":
                    EVENT_FEATURE_MAP[event_name],

                "device_type":
                    device_type
            })


    # =====================================================
    # 9. Create DataFrame
    # =====================================================

    if not event_records:
        break


    events_df = pd.DataFrame(
        event_records
    )


    # =====================================================
    # 10. Event IDs
    # =====================================================

    start_id = (
        total_events_generated + 1
    )

    events_df.insert(
        0,
        "event_id",
        [
            f"E{i:010d}"
            for i in range(
                start_id,
                start_id + len(events_df)
            )
        ]
    )


    # =====================================================
    # 11. Validation
    # =====================================================

    if not events_df["event_id"].is_unique:

        raise ValueError(
            "Duplicate event_id detected."
        )


    if not events_df["session_id"].isin(
        sessions_chunk["session_id"]
    ).all():

        raise ValueError(
            "Invalid session_id detected."
        )


    if not events_df["user_id"].isin(
        sessions_chunk["user_id"]
    ).all():

        raise ValueError(
            "Invalid user_id detected."
        )


    # =====================================================
    # 12. Write chunk to CSV
    # =====================================================

    events_df.to_csv(
        OUTPUT_FILE,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False
    )

    first_chunk = False


    # =====================================================
    # 13. Update counters
    # =====================================================

    total_sessions_processed += len(
        sessions_chunk
    )

    total_events_generated += len(
        events_df
    )


    print(
        f"Sessions processed : "
        f"{total_sessions_processed:,}"
    )

    print(
        f"Events generated   : "
        f"{total_events_generated:,}"
    )


    # =====================================================
    # 14. Stop if hard limit reached
    # =====================================================

    if total_events_generated >= MAX_EVENTS:

        print(
            "\nMaximum event limit reached."
        )

        break


# =========================================================
# 15. Final checks
# =========================================================

if not OUTPUT_FILE.exists():

    raise RuntimeError(
        "product_events.csv was not created."
    )


# =========================================================
# 16. Final summary
# =========================================================

print("\n" + "=" * 65)
print("PRODUCT EVENTS DATASET CREATED")
print("=" * 65)

print(
    f"Sessions processed : "
    f"{total_sessions_processed:,}"
)

print(
    f"Total events       : "
    f"{total_events_generated:,}"
)

print(
    f"Events/session     : "
    f"{total_events_generated / total_sessions_processed:.2f}"
)

print(
    f"Output file        : "
    f"{OUTPUT_FILE}"
)

print(
    f"\nHard limit         : "
    f"{MAX_EVENTS:,}"
)

print("\nEvent types:")

for event in EVENT_FEATURE_MAP:

    print(f"  - {event}")

print("\nGeneration completed successfully.")