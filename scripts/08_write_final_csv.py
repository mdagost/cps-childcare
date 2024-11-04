import os

import pandas as pd

from cps_childcare.utils import get_all_records


AIRTABLE_BASE_ID = "appPfxeoBduSJLC67"
AIRTABLE_CHILDCARE_TABLE_NAME = "tblsiTlNXf5uzZF6c"
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]


schools = get_all_records(AIRTABLE_BASE_ID, AIRTABLE_CHILDCARE_TABLE_NAME, AIRTABLE_API_KEY)
data = pd.DataFrame([school["fields"] for school in schools])

columns_name_map = {
    "Name": "Elementary School",
    "Address": "Address",
    "neighborhood": "Neighborhood",
    "schoolHours": "School Hours",
    "earliestDropOffTime": "Earliest Drop Off Time",
    "afterSchoolHours": "After School Hours",
    "Grades_Short": "Grades",
    "Phone": "Phone",
    "websiteURL": "Website",
    "contact_url": "Contact Page",
    "provides_before_care": "Provides Before Care",
    "provides_after_care": "Provides After Care",
    "before_care_start_time": "Before Care Start Time",
    "before_care_provider": "Before Care Provider",
    "after_care_end_time": "After Care End Time",
    "after_care_provider": "After Care Provider",
    "google_maps_coordinates": "latlon"
}

data = data[columns_name_map.keys()]
data = data.rename(columns=columns_name_map)

data["lat"] = data["latlon"].apply(lambda latlong: latlong.split(",")[0] if latlong else None)
data["lon"] = data["latlon"].apply(lambda latlong: latlong.split(",")[1] if latlong else None)
data = data.drop(columns=["latlon"])

data.to_csv("data/final_childcare_dataset.csv", index=False)