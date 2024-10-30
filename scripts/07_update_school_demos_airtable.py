import os

import pandas as pd

from cps_childcare.utils import update_record


AIRTABLE_BASE_ID = "appPfxeoBduSJLC67"
AIRTABLE_RAW_DATA_TABLE_NAME = "tblHoR7kZU8IzuKJb"
AIRTABLE_CHILDCARE_TABLE_NAME = "tblsiTlNXf5uzZF6c"
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]

["isTitle1Eligible", "studentCount", "studentCountLowIncome",
 "studentCountBlack", "studentCountHispanic", "studentCountWhite"]
schools = pd.read_csv("../data/cps_schools_contacts.csv")
    update_record(record.school_id, new_record_fields, AIRTABLE_BASE_ID, AIRTABLE_RAW_DATA_TABLE_NAME, AIRTABLE_API_KEY)
