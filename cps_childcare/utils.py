from textwrap import dedent
from airtable import Airtable


def get_all_records(airtable_base_id, table, airtable_api_key):
    airtable = Airtable(airtable_base_id, table, airtable_api_key)
    return airtable.get_all()


def update_record(school_id, new_fields_dict, airtable_base_id, table, airtable_api_key):
    airtable = Airtable(airtable_base_id, table, airtable_api_key)

    # get the existing record
    filter_formula = f"{{School_ID}}=\"{school_id}\""
    existing_records = airtable.get_all(formula=filter_formula)

    assert len(existing_records) == 1, f"Found {len(existing_records)} records for school {school_id}."

    existing_record = existing_records[0]
    record_id = existing_record["id"]

    # merge the new fields with the existing fields
    updated_fields = {**existing_record["fields"], **new_fields_dict}
    del updated_fields["google_maps_coordinates"]
    print(updated_fields)

    # update the record in airtable
    airtable.update(record_id, updated_fields, typecast=True)
