"""All TRANA demo assumptions live here. Do not duplicate these values elsewhere."""
from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("TRANA_DATA_DIR", ROOT_DIR / "backend" / "data"))
PHOTO_DIR = DATA_DIR / "photos"
DATABASE_URL = os.getenv("TRANA_DATABASE_URL", f"sqlite:///{DATA_DIR / 'trana.sqlite3'}")

# SHARED time configuration
SCENARIO_MINUTE_SECONDS = int(os.getenv("SCENARIO_MINUTE_SECONDS", "60"))

# SECTION A — Person A owns these demo assumptions.
SOURCE_TRUST = {
    "verification_report": 1.0,
    "camp_lead": 0.8,
    "volunteer": 0.8,
    "simulated_sensor": 0.7,
    "citizen": 0.5,
    "system": 1.0,
    "coordinator": 1.0,
}
FRESHNESS_HALF_LIFE_MINUTES = {
    "road_status": 4, "water_level": 3, "camp_status": 8,
    "stock_report": 8, "shortage_request": 6, "verification_report": 8,
}
CONFIDENCE_CONFIRMED = 0.70
CONFIDENCE_UNCONFIRMED = 0.40
EXPECTED_REPORT_INTERVAL_MINUTES = 2
SILENCE_MULTIPLIER = 1.5
VOLUNTEER_LOCATION_MAX_AGE_MINUTES = 15
ALLOCATION_TARGET_DAYS = 3
MINIMUM_GUARANTEE_DAYS = 1
WATER_LITRES_PER_PERSON_DAY = 15
FOOD_RATIONS_PER_PERSON_DAY = 1
SCORE_WEIGHTS = {
    "supply_shortfall": 0.40, "vulnerable_share": 0.25,
    "time_since_delivery": 0.20, "access_difficulty": 0.15,
}
TIER_HIGH = 60
TIER_MEDIUM = 30
TASK_ACCEPT_TIMEOUT_MINUTES = 3
TASK_COMPLETE_TIMEOUT_MINUTES = 10
CORROBORATION_AGREEMENT_MULTIPLIER = 1.2
CORROBORATION_CONFLICT_MULTIPLIER = 0.5

JOIN_CODES = {
    "CAMP-A1": {"role": "camp_lead", "user_id": "lead-a1", "camp_id": "camp-a"},
    "CAMP-B1": {"role": "camp_lead", "user_id": "lead-b1", "camp_id": "camp-b"},
    "VOL-01": {"role": "volunteer", "user_id": "vol-01", "camp_id": None},
    "VOL-02": {"role": "volunteer", "user_id": "vol-02", "camp_id": None},
    "COORD-01": {"role": "coordinator", "user_id": "coord-01", "camp_id": None},
}

# SECTION C — Person C owns this section only.
# TODO(decision): scenario-specific settings are loaded from /scenario at runtime.
