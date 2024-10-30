import json
import os
import re
import time
from collections import defaultdict
from random import uniform

import pandas as pd
import requests


def get_schools_json():
    """
    Get a list of all CPS schools with some useful data about them.
    This URL comes from loading the map at https://schoolinfo.cps.edu/schoollocator/
    and then looking at the activity in the network tab of chrome devtools
    there are a ton of school features here, but notably NOT the email address OR
    the URL of the school's website.
    """
    CPS_API_URL = "https://api.cps.edu/maps/cps/GeoJSON?mapname=SCHOOL&year=2025"
    CACHE_FILE = "/Users/mdagostino/cps_schools.json"

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    else:
        response = requests.get(CPS_API_URL)
        with open(CACHE_FILE, "w") as f:
            json.dump(response.json()["features"], f)
        return response.json()


def get_school_profile_data(school_id):
    """
    For each school, we have a school_id in our dataset already.  We can query another CPS endpoint to get
    some more info for each school.
    This URL comes from visiting a school profile page like https://www.cps.edu/schools/schoolprofiles/400052
    and then looking at the activity in the network tab of chrome devtools.
    It's got some useful info (but NOT the email address), BUT it does have the shool's website URL.
    It appears to be the API endpoint documented here: https://api.cps.edu/schoolprofile/Help/Api/GET-CPS-SingleSchoolProfile_SchoolID
    """
    CPS_SCHOOL_PROFILE_API_BASE = "https://www.cps.edu/api/schoolprofile/singleschoolprofile?SchoolID="
    
    school_profile_url = f"{CPS_SCHOOL_PROFILE_API_BASE}{school_id}"

    response = requests.get(school_profile_url)

    return response.json()


def clean_school_url(school_website_url):
    # make sure the url starts with http
    if not re.match(r"^https?", school_website_url):
        school_website_url = f"http://{school_website_url}"

    # get rid of any trailing slash in the url
    school_website_url = re.sub(r"/$", "", school_website_url)

    return school_website_url


def get_school_contact_page(school_website_url):
    """
    Try 3 common patterns for the school's contact form on its website.  Also, a very large
    percentage of sites are made by two vendors--Edlio and Eductional Networks--so we try
    to figure that out too.
    """
    contact_url_1 = f"{school_website_url}/apps/contact"
    contact_url_2 = f"{school_website_url}/contact/"
    contact_url_3 = f"{school_website_url}/contact.html"

    for contact_url_try in [contact_url_1, contact_url_2, contact_url_3]:
        try:
            response = requests.get(contact_url_try, headers=headers)
            if response.status_code == 200: 
                is_edlio = "Edlio" in response.text
                # use a regex here because we can have newlines and stuff between the two words
                is_educational_networks = re.search("Educational\s*Networks", response.text, re.IGNORECASE) is not None
                return contact_url_try, response.text, is_edlio, is_educational_networks
        except requests.exceptions.ConnectionError:
            pass

    return None, None, None, None


def get_emails_from_contact_page(contact_page_text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return list(set(re.findall(email_pattern, contact_page_text)))


if __name__ == "__main__":
    # some CPS school /contact pages give 403's without a proper header
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    }
    
    schools = get_schools_json()

    # get the data into a pandas dataframe
    data = pd.DataFrame(schools)
    
    # explode the json
    schools_lat_longs = pd.json_normalize(data.geometry)
    schools_features = pd.json_normalize(data.properties)
    schools = pd.concat([schools_features, schools_lat_longs[["coordinates"]]], axis=1)

    profile_data = defaultdict(list)
    for idx, school in schools.iterrows():
        school_name = school.Name
        school_id = school.School_ID
        school_type = school.Type

        print(f"{school_name}: {school_id}: {school_type}")

        school_profile_data = get_school_profile_data(school_id)

        if school_profile_data is not None:
            keys_to_print = ["schoolHours", "afterSchoolHours", "earliestDropOffTime",
                            "phone", "gradesOffered", "websiteURL",
                            "isTitle1Eligible", "studentCount", "studentCountLowIncome",
                            "studentCountBlack", "studentCountHispanic", "studentCountWhite"]
            print(f"Index = {idx}")
            for key_to_print in keys_to_print:
                value = school_profile_data[key_to_print]
                profile_data[key_to_print].append(value)
            print(value)

            school_website_url = clean_school_url(school_profile_data["websiteURL"])
            emails = []

            contact_url, contact_page_text, is_edlio, is_educational_networks = get_school_contact_page(school_website_url)
            print(contact_url)

            if contact_url is not None and not is_edlio and not is_educational_networks:
                emails = get_emails_from_contact_page(contact_page_text)
                print(",".join(emails))
        else:
            print("No school profile data found!!")
            for key_to_print in keys_to_print:
                profile_data[key_to_print].append(None)
            contact_url, is_edlio, is_educational_networks = None, None, None
            emails = []

        profile_data["contact_url"].append(contact_url)
        profile_data["is_edlio"].append(is_edlio)
        profile_data["is_educational_networks"].append(is_educational_networks)
        profile_data["contact_emails"].append("|".join(emails))

        print("**************************\n\n")

        # sleep a random amount of time between 1s and 5s
        time.sleep(uniform(1, 5))

    # dump the final results to csv
    pd.concat([schools, pd.DataFrame(profile_data)], axis=1).to_csv("data/cps_schools_contacts.csv")

