import os
from textwrap import dedent

from openai import OpenAI
from sqlalchemy import text
from sqlmodel import select, Session

from cps_childcare.cps_data_models import (ChildcareOpenAIRecord, ChildcareOpenAIResponse,
    CitationSnippet, CombinedChildcareOpenAIRecord, CombinedChildcareOpenAIResponse, CrawlerRecord)
from cps_childcare.database import engine


def extract_care_page_details(client, page: CrawlerRecord, model="gpt-4o-mini", prompt_version="v1"):
    prompt_v1 = f"""
    Here is an elementary school webpage. If present, extract information about before and after school child care.
    Follow these rules:
    - We ONLY care about before or after care CHILDCARE programs, not general instructions about what students are supposed to do before and after school, or about summer programs, or about sports.
    - Don't include info on summer camps or day camps.
    - Sometimes these programs are called "OST", "Out of School Time", or "Right at School" programs.
    - For the fields "before_care_quote_snippet" and "after_care_quote_snippet", return the EXACT QUOTED TEXT from the webpage "Content" that is the most relevant snippet to your answer.  DO NOT CHANGE ANY WORDS.

    ## Webpage
    #URL:
    {page.page_url}
    #Description:
    {page.page_title}
    #Content to Quote From:
    "{page.markdown}"

    ## Answer:
    """

    completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": "You are an AI expert tasked with understanding elementary school websites."},
                {"role": "user", "content": prompt_v1}
            ],
            temperature=0.0,
            response_format=ChildcareOpenAIResponse
        )

    return ChildcareOpenAIResponse.model_validate_json(completion.choices[0].message.content)


def combine_care_page_details(client, school_id, model="gpt-4o-mini", prompt_version="v2"):
    school_pages = get_all_school_extracted_pages(school_id)
    school_pages = list(filter(is_current_page, school_pages))

    if len(school_pages) == 0:
        return None

    prompt_v2 = """
    Here is a numbered list of json objects extracted from webpages about a single elementary school.  Use the
    information to synthesize a single, high quality overview of the school's before and after school child care program.
    - Prefer pages where the "before_care_quote_snippet_verified" and "after_care_quote_snippet_verified" fields are True over ones where they are False.
    - If there are multiple pages that contain the same information, prefer the one with the highest quality "before_care_quote_snippet_verified" and "after_care_quote_snippet_verified" fields.
    - If there are multiple pages that contain the same information, prefer the one with the most recent "webpage_year" field.
    - You MUST cite your sources by listing the source number in "before_care_citations" and "after_care_citations".

    ## Webpages
    """

    context_fields = ["page_url", "webpage_year",
                      "provides_before_care", "before_care_start_time", "before_care_provider", "before_care_quote_snippet", "before_care_quote_snippet_verified",
                      "provides_after_care", "after_care_end_time", "after_care_provider", "after_care_quote_snippet", "after_care_quote_snippet_verified"]
    context = ""
    citation_urls = []
    citation_before_care_snippets = []
    citation_after_care_snippets = []
    for num, page in enumerate(school_pages):
        context_dict = {field: getattr(page, field) for field in context_fields}
        context += f"[{num}] {context_dict}\n\n"
        citation_urls.append(page.page_url)
        citation_before_care_snippets.append(page.before_care_quote_snippet)
        citation_after_care_snippets.append(page.after_care_quote_snippet)

    full_prompt = dedent(prompt_v2) + context + "\n\n## Answer:"

    completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": "You are an AI expert tasked with understanding elementary and high school websites."},
                {"role": "user", "content": full_prompt}
            ],
            #temperature=0.0,
            response_format=CombinedChildcareOpenAIResponse
        )

    response = CombinedChildcareOpenAIResponse.model_validate_json(completion.choices[0].message.content)

    # go from citation number to citation text to make sure it's exact
    # instead of trusting what gpt returns here (we trust the numbers though)
    response.before_care_citation_snippets = []
    response.after_care_citation_snippets = []

    if response.before_care_citations:
        for before_care_citation in response.before_care_citations:
            response.before_care_citation_snippets.append(
                CitationSnippet(
                    url=str(citation_urls[before_care_citation]),
                    snippet=str(citation_before_care_snippets[before_care_citation])
                )
            )
    if response.after_care_citations:
        for after_care_citation in response.after_care_citations:
            response.after_care_citation_snippets.append(
                CitationSnippet(
                    url=str(citation_urls[after_care_citation]),
                    snippet=str(citation_after_care_snippets[after_care_citation])
                )
            )

    return response


def get_pages_to_extract():
    with Session(engine) as session:
        # only get pages that haven't been extracted yet
        query = text(
        f"""
        WITH crawler_records_by_model AS (
            SELECT *,
                row_number() OVER (PARTITION BY school_id, page_url, openai_model_name, prompt_version ORDER BY created_at DESC) AS row
            FROM crawleropenairecord
        )

        SELECT cr.*
        FROM crawler_records_by_model o
        JOIN crawlerrecord cr
            ON o.school_id = cr.school_id
            AND o.page_url = cr.page_url
        LEFT JOIN childcareopenairecord co
            ON o.school_id = co.school_id
            AND o.page_url = co.page_url
        WHERE row = 1
            AND o.openai_model_name = 'gpt-4o-mini'
            AND o.prompt_version = 'v1'
            AND o.before_or_after_care_details != ''
            AND co.id IS NULL
        """
        )
        result = session.exec(query)
        pages = result.fetchall()
        pages = [CrawlerRecord.model_validate(page) for page in pages]

    return list(pages)


# get the schools we haven't combined yet
def get_schools_to_combine(prompt_version="v2"):
    with Session(engine) as session:
        query = select(ChildcareOpenAIRecord.school_id).distinct()
        result = session.exec(query)
        all_schools = result.fetchall()

        query = (select(CombinedChildcareOpenAIRecord.school_id)
                 .where(CombinedChildcareOpenAIRecord.prompt_version == prompt_version)
                ).distinct()
        result = session.exec(query)
        combined_schools = result.fetchall()

    schools_remaining = set(all_schools).difference(set(combined_schools))

    return schools_remaining


def get_all_school_extracted_pages(school_id):
    with Session(engine) as session:
        query = (select(ChildcareOpenAIRecord)
                 .where(ChildcareOpenAIRecord.school_id == school_id)
                 .where((ChildcareOpenAIRecord.provides_before_care == True) |
                        (ChildcareOpenAIRecord.provides_after_care == True)))
        result = session.exec(query)
        pages = result.fetchall()
        pages = [ChildcareOpenAIRecord.model_validate(page) for page in pages]

    return pages


# returns true if the page is from the current school year
def is_current_page(page: ChildcareOpenAIRecord) -> bool:
    # our default is that it's current
    if page.webpage_year is None:
        return True

    OLD_YEARS = ["08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22"]
    YEAR_PATTERNS_0 = [f"20{y}" for y in OLD_YEARS]
    YEAR_PATTERNS_1 = [f"20{y1}-20{y2}" for y1, y2 in zip(OLD_YEARS, OLD_YEARS[1:])]
    YEAR_PATTERNS_2 = [f"20{y1}/20{y2}" for y1, y2 in zip(OLD_YEARS, OLD_YEARS[1:])]
    YEAR_PATTERNS_3 = [f"20{y1}-{y2}" for y1, y2 in zip(OLD_YEARS, OLD_YEARS[1:])]
    YEAR_PATTERNS_4 = [f"20{y1}/{y2}" for y1, y2 in zip(OLD_YEARS, OLD_YEARS[1:])]
    YEAR_PATTERNS_5 = ["2018-2020"]
    YEAR_PATTERNS = YEAR_PATTERNS_0 + YEAR_PATTERNS_1 + YEAR_PATTERNS_2 + YEAR_PATTERNS_3 + YEAR_PATTERNS_4 + YEAR_PATTERNS_5

    # replace spaces and "en dashes" with normal dashes
    webpage_year = page.webpage_year.replace(" ", "").replace("–", "-")
    for pattern in YEAR_PATTERNS:
        if webpage_year == pattern:
            return False
    return True


client = OpenAI(api_key=os.getenv("CPS_OPENAI_API_KEY"))

pages = get_pages_to_extract()
print(f"Sending {len(pages)} pages to OpenAI...")

MODEL = "gpt-4o-mini"
PROMPT_VERSION = "v1"

for page_num, page in enumerate(pages):
    extracted = extract_care_page_details(client, page, model=MODEL)

    before_care_quote_snippet_verified, after_care_quote_snippet_verified = None, None

    cleaned_markdown = page.markdown.replace("\n", "").replace(" ", "")

    if extracted.before_care_quote_snippet:
        cleaned_before_care_quote_snippet = extracted.before_care_quote_snippet.replace("\n", "").replace(" ", "")
        before_care_quote_snippet_verified = cleaned_before_care_quote_snippet in cleaned_markdown
    if extracted.after_care_quote_snippet:
        cleaned_after_care_quote_snippet = extracted.after_care_quote_snippet.replace("\n", "").replace(" ", "")
        after_care_quote_snippet_verified = cleaned_after_care_quote_snippet in cleaned_markdown

    result = {
        "school_id": page.school_id,
        "page_url": page.page_url,
        "openai_model_name": MODEL,
        "prompt_version": PROMPT_VERSION,
        **extracted.model_dump(),
        "before_care_quote_snippet_verified": before_care_quote_snippet_verified,
        "after_care_quote_snippet_verified": after_care_quote_snippet_verified,
    }

    with Session(engine) as session:
        session.add(ChildcareOpenAIRecord.model_validate(result))
        session.commit()

    print(f"{page_num} / {len(pages)}: {page.page_url}")
    print(result)


school_ids = get_schools_to_combine()
print(f"Combining data for {len(school_ids)} schools...")

MODEL = "gpt-4o-mini"
PROMPT_VERSION = "v2"

for num, school_id in enumerate(school_ids):
    combined = combine_care_page_details(client, school_id, model=MODEL, prompt_version=PROMPT_VERSION)

    if combined is None:
        print(f"No pages to combine for school {school_id}")
        continue

    result = {
        "school_id": school_id,
        "openai_model_name": MODEL,
        "prompt_version": PROMPT_VERSION,
        **combined.model_dump(),
    }

    with Session(engine) as session:
        session.add(CombinedChildcareOpenAIRecord.model_validate(result))
        session.commit()

    print(f"{num} / {len(school_ids)}: {school_id}")
    print(result)