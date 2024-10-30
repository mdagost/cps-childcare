import json
import os

from shapely.geometry import Point, shape

from cps_childcare.utils import get_all_records, update_record


AIRTABLE_BASE_ID = "appPfxeoBduSJLC67"
AIRTABLE_CHILDCARE_TABLE_NAME = "tblsiTlNXf5uzZF6c"
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
# downloaded from https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Community-Areas-current-/cauq-8yn6
NEIGHBORHOOD_FILE = "data/Boundaries - Community Areas (current).geojson"


def get_neighborhood(lat, lon, geojson):
    # shapely uses (lon, lat) order
    point = Point(lon, lat)

    for feature in geojson["features"]:
        geometry = shape(feature["geometry"])
        if geometry.contains(point):
            return feature["properties"]["community"].title()

    return None


with open(NEIGHBORHOOD_FILE) as f:
    geojson = json.load(f)

schools = get_all_records(AIRTABLE_BASE_ID, AIRTABLE_CHILDCARE_TABLE_NAME, AIRTABLE_API_KEY)
for school in schools:
    lat, lon = school["fields"]["google_maps_coordinates"].split(",")
    lat, lon = float(lat), float(lon)

    school_id = school["fields"]["School_ID"]
    update = {"neighborhood": get_neighborhood(lat, lon, geojson)}

    print(school_id, update)
    update_record(school_id, update, AIRTABLE_BASE_ID, AIRTABLE_CHILDCARE_TABLE_NAME, AIRTABLE_API_KEY)
