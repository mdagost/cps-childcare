# pyright: reportMissingImports=false
import os
import random

from firecrawl.firecrawl import FirecrawlApp
from sqlmodel import select, Session

from cps_childcare.cps_data_models import CrawlerRecord
from cps_childcare.database import engine
from cps_childcare.utils import get_all_records


def bulk_insert_crawler_records(records):
    with Session(engine) as session:
        session.bulk_insert_mappings(CrawlerRecord, records)
        session.commit()


def get_completed_school_ids():
    with Session(engine) as session:
        school_ids = session.exec(
            select(CrawlerRecord.school_id).distinct()
        )

        return list(school_ids)
    

def extract_crawled_data(crawled_data):
    metadata = crawled_data["metadata"]

    record = {}
    record["page_title"] = metadata.get("title", None)
    record["page_url"] = metadata["sourceURL"]
    record["description"] = metadata.get("description", None)
    record["status_code"] = str(metadata["statusCode"])
    record["markdown"] = crawled_data.get("markdown", None)
    html = crawled_data.get("html", None)
    if html and len(html) < 100_000:
        record["html"] = html
    else:
        record["html"] = None

    return record


AIRTABLE_BASE_ID = "appPfxeoBduSJLC67"
AIRTABLE_RAW_TABLE_NAME = "tblHoR7kZU8IzuKJb"

airtable_api_key = os.environ["AIRTABLE_API_KEY"]

fc = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

schools = get_all_records(AIRTABLE_BASE_ID, AIRTABLE_RAW_TABLE_NAME, airtable_api_key)

# don't do schools we've already crawled

completed_schools = get_completed_school_ids()
schools = [s for s in schools if s["fields"]["School_ID"] not in completed_schools]

# MANUALLY CHOOSE THE SCHOOLS TO SUBMIT
#MANUAL_SCHOOL_IDS = [
#    609990,
#]
#schools = [s for s in schools if s["fields"]["School_ID"] in MANUAL_SCHOOL_IDS]


random.shuffle(schools)
for school in schools:
    if "websiteURL" not in school["fields"]:
        continue
    
    crawl_url = school["fields"]["websiteURL"]
    print(f"Crawling {crawl_url}...")

    try:
        crawl_result = fc.crawl_url(
            crawl_url,
            params={"limit": 300,
                "excludePaths": ["calendar", "newsletter", "/images", "/Health Forms*/*", "/reminders/*",
                                 "/news--updates/*", "/news/archives/*", "/bateman-art-blog/*"
                                 "/apps/events/*", "/event/*", "/events/*", "/board_minutes/*",
                                 "/2018/*", "/2019/*", "/2020/*", "/2021/*", "/2022/*", "/2023/*",
                                 "/enroll21-22/*", "/classrooms21-22/*/*", "/classrooms1920/*/*",
                                 "/Classrooms2324/*/*", "/Classrooms22-23/*/*/",
                                 "/gallery/*/*", "/images/*/*",
                                 "/uploads/.*\.png", "/uploads/.*\.jpg",
                                 "/lsc/archives/*", "/parents/archives/*",
                                 "/teachers-staff/*", "/category/teachers-staff/*",
                                 "/athletics-2/*", "/category/athletics-2/*",
                                  "/performing-fine-arts-2/*", "/category/performing-fine-arts-2/*",
                                  "/south-loop-scoop/*", "/the-south-loop-school-scoop/*",
                                  "/author/*", "/past-special-events/*", "/past-reminders/*"],
                "scrapeOptions": {
                    "formats": ["markdown", "html"],
                    "onlyMainContent": True
                    }
                },
            poll_interval=10
        )
    except Exception as e:
        print(f"Crawl failed for {crawl_url}!!")
        print(e)
        continue

    if crawl_result["success"]:
        print(f"Crawled {crawl_result['total']} urls for {crawl_url}...")
        records = []
        for crawled_data in crawl_result["data"]:
            if crawled_data:
                record = extract_crawled_data(crawled_data)
                record["index"] = school["fields"]["Index"]
                record["school_name"] = school["fields"]["Name"]
                record["school_id"] = school["fields"]["School_ID"]
                record["school_type"] = school["fields"]["Type"]
                records.append(record)

        # insert the full batch into the database
        bulk_insert_crawler_records(records)
    else:
        print(f"Crawl failed for {crawl_url}!!")
