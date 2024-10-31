import os

from sqlmodel import select, Session

from cps_childcare.cps_data_models import CombinedChildcareOpenAIRecord
from cps_childcare.utils import update_record
from cps_childcare.database import engine


AIRTABLE_BASE_ID = "appPfxeoBduSJLC67"
AIRTABLE_CHILDCARE_TABLE_NAME = "tblsiTlNXf5uzZF6c"
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]


with Session(engine) as session:
    combined_records = session.exec(
        select(CombinedChildcareOpenAIRecord)
        .where(CombinedChildcareOpenAIRecord.prompt_version == "v2")
    ).all()

keys_to_append = [
    "provides_before_care",
    "provides_after_care",
    
    "before_care_start_time",
    "before_care_provider",
    "before_care_citations",
    "before_care_citation_snippets",

    "after_care_end_time",
    "after_care_provider",
    "after_care_citations",
    "after_care_citation_snippets"
]
for record in combined_records:
    filtered_records = {k: v for k, v in record.model_dump().items() if k in keys_to_append}
    update_record(record.school_id, filtered_records, AIRTABLE_BASE_ID, AIRTABLE_CHILDCARE_TABLE_NAME, AIRTABLE_API_KEY)
