import os

import pandas as pd

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

        print("Updating raw...")
        update_record(school_id, new_record_fields, AIRTABLE_BASE_ID, AIRTABLE_RAW_DATA_TABLE_NAME, AIRTABLE_API_KEY)

        print("Updating childcare...")
        update_record(school_id, new_record_fields, AIRTABLE_BASE_ID, AIRTABLE_CHILDCARE_TABLE_NAME, AIRTABLE_API_KEY)
        break

childcare_schools = get_all_records(AIRTABLE_BASE_ID, AIRTABLE_CHILDCARE_TABLE_NAME, AIRTABLE_API_KEY)
childcare_schools = pd.DataFrame([cs["fields"] for cs in childcare_schools])

neighborhood_counts = childcare_schools.groupby("neighborhood").sum()[new_fields].reset_index()
neighborhood_counts["neighborhood_low_income_student_pct"] = neighborhood_counts["studentCountLowIncome"] / neighborhood_counts["studentCount"]
neighborhood_counts["neighborhood_black _student_pct"] = neighborhood_counts["studentCountBlack"] / neighborhood_counts["studentCount"]
neighborhood_counts["neighborhood_hispanic_student_pct"] = neighborhood_counts["studentCountHispanic"] / neighborhood_counts["studentCount"]
neighborhood_counts["neighborhood_white_student_pct"] = neighborhood_counts["studentCountWhite"] / neighborhood_counts["studentCount"]

print(neighborhood_counts.head())