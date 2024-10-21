from textwrap import dedent
from airtable import Airtable


def get_all_records(airtable_base_id, table, airtable_api_key):
    airtable = Airtable(airtable_base_id, table, airtable_api_key)
    return airtable.get_all()


def upsert_record(record, airtable_base_id, table, airtable_api_key):
    airtable = Airtable(airtable_base_id, table, airtable_api_key)

    # check if the record exists based on multiple fields
    filter_formula = "AND(" + ",".join([f"{{Title}}=\"{record['Title']}\"", f"{{Company}}=\"{record['Company']}\""]) + ")"
    existing_records = airtable.get_all(formula=filter_formula)

    if existing_records:
        print(f"Record already exists: {existing_records}")
    else:
        airtable.insert(record, typecast=True)
