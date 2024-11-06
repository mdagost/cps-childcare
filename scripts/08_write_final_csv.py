import json
import os

import pandas as pd

from cps_childcare.utils import get_all_records


AIRTABLE_BASE_ID = "appPfxeoBduSJLC67"
AIRTABLE_CHILDCARE_TABLE_NAME = "tblsiTlNXf5uzZF6c"
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]


schools = get_all_records(AIRTABLE_BASE_ID, AIRTABLE_CHILDCARE_TABLE_NAME, AIRTABLE_API_KEY)
data = pd.DataFrame([school["fields"] for school in schools])

data = data[data.Type.isin(["Elementary School", "ElementaryCharter"])]

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
    "before_care_citation_snippets": "Before Care Info",
    "after_care_end_time": "After Care End Time",
    "after_care_provider": "After Care Provider",
    "after_care_citation_snippets": "After Care Info",
    "google_maps_coordinates": "latlon"
}

data = data[columns_name_map.keys()]
data = data.rename(columns=columns_name_map)

data["lat"] = data["latlon"].apply(lambda latlong: latlong.split(",")[0] if latlong else None)
data["lon"] = data["latlon"].apply(lambda latlong: latlong.split(",")[1] if latlong else None)
data = data.drop(columns=["latlon"])

data["Phone"] = data["Phone"].apply(lambda phone: phone.replace(")", ") ") if phone else None)
data["Grades"] = data["Grades"].apply(lambda grades: grades[0] if grades else None)

# handle the citations
def format_citations(citations):
    if citations:
        try:
            citations = json.loads(citations)
        except TypeError:
            return ""
        
        citation_str = ""
        for num, citation in enumerate(citations):
            link = f'"{citation["snippet"]}" <a href="{citation["url"]}" target="_blank" rel="noopener noreferrer">[{num+1}]</a>'
            citation_str += link + "\n"
        
        return citation_str
    
    return ""

data["Before Care Info"] = data["Before Care Info"].apply(lambda citations: format_citations(citations))
data["After Care Info"] = data["After Care Info"].apply(lambda citations: format_citations(citations))

data = data.sort_values("Elementary School")

data.to_csv("data/final_childcare_dataset.csv", 
          index=False,              # Don't write row numbers
          quoting=1,               # Quote all non-numeric fields (csv.QUOTE_ALL)
          quotechar='"',           # Use double quotes
          encoding='utf-8',        # Use UTF-8 encoding
          na_rep='',              # Empty string for NA/NaN values
          date_format='%Y-%m-%d'   # ISO format for dates if any
)