import math
import os

import pandas as pd
from sqlmodel import Session

from cps_childcare.cps_data_models import Neighborhood
from cps_childcare.database import engine
from cps_childcare.utils import get_all_records, update_record


AIRTABLE_BASE_ID = "appPfxeoBduSJLC67"
AIRTABLE_RAW_DATA_TABLE_NAME = "tblHoR7kZU8IzuKJb"
AIRTABLE_CHILDCARE_TABLE_NAME = "tblsiTlNXf5uzZF6c"
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
UPDATE_RAW_RECORDS = False

schools = pd.read_csv("data/cps_schools_contacts.csv")

new_fields = ["isTitle1Eligible", "studentCount", "studentCountLowIncome",
                "studentCountBlack", "studentCountHispanic", "studentCountWhite"]

if UPDATE_RAW_RECORDS:
    for index, row in schools.iterrows():
        school_id = row["School_ID"]
        new_record_fields = {field: row[field] for field in new_fields}

        # replace NaNs with None to make Airtable happy
        for field in new_fields:
            if math.isnan(new_record_fields[field]):
                new_record_fields[field] = None

        update_record(school_id, new_record_fields, AIRTABLE_BASE_ID, AIRTABLE_RAW_DATA_TABLE_NAME, AIRTABLE_API_KEY)
        update_record(school_id, new_record_fields, AIRTABLE_BASE_ID, AIRTABLE_CHILDCARE_TABLE_NAME, AIRTABLE_API_KEY)

all_schools = get_all_records(AIRTABLE_BASE_ID, AIRTABLE_RAW_DATA_TABLE_NAME, AIRTABLE_API_KEY)
all_schools = pd.DataFrame([school["fields"] for school in all_schools])

neighborhood_counts = all_schools.groupby("neighborhood").sum()[new_fields].reset_index()

neighborhood_counts = neighborhood_counts.drop("isTitle1Eligible", axis=1)

rename_map = {
    "studentCount": "student_count",
    "studentCountLowIncome": "low_income_student_count",
    "studentCountBlack": "black_student_count",
    "studentCountHispanic": "hispanic_student_count",
    "studentCountWhite": "white_student_count"
}

neighborhood_counts = neighborhood_counts.rename(columns=rename_map)

neighborhood_counts["low_income_student_pct"] = neighborhood_counts["low_income_student_count"] / neighborhood_counts["student_count"]
neighborhood_counts["black_student_pct"] = neighborhood_counts["black_student_count"] / neighborhood_counts["student_count"]
neighborhood_counts["hispanic_student_pct"] = neighborhood_counts["hispanic_student_count"] / neighborhood_counts["student_count"]
neighborhood_counts["white_student_pct"] = neighborhood_counts["white_student_count"] / neighborhood_counts["student_count"]

print(neighborhood_counts.head())

for index, row in neighborhood_counts.iterrows():
    neighborhood = Neighborhood.model_validate(row.to_dict())

    print(neighborhood)

    with Session(engine) as session:
        session.add(neighborhood)
        session.commit()
