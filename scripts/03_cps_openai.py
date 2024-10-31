# pyright: reportMissingImports=false
import os
import random
from textwrap import dedent

import tiktoken
from openai import OpenAI
from sqlalchemy import text
from sqlmodel import select, Session
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_random_exponential

from cps_childcare.cps_data_models import CrawlerRecord, CrawlerOpenAIRecord, CrawlerOpenAIResponse
from cps_childcare.database import engine


def get_pages(model_name: str = "gpt-4o-mini", prompt_version: str = None, evals: bool = False):
    with Session(engine) as session:
        if not evals:
            # get pages we haven't sent to openai yet
            pages = session.exec(
            select(CrawlerRecord)
            .outerjoin(CrawlerOpenAIRecord,
                       (CrawlerRecord.school_id == CrawlerOpenAIRecord.school_id) & 
                       (CrawlerRecord.page_url == CrawlerOpenAIRecord.page_url) &
                       (CrawlerOpenAIRecord.openai_model_name == model_name)
            )
            .where(CrawlerRecord.status_code == 200)
            .where(CrawlerRecord.markdown.is_not(None))
            .where(CrawlerOpenAIRecord.id == None)
            )
        else:
            # Query raw table without SQLAlchemy model
            query = text(
            f"""
            WITH crawler_records_by_model AS (
                SELECT * FROM crawleropenairecord
                WHERE openai_model_name = '{model_name}'
                    AND prompt_version = '{prompt_version}'
            )
            
            SELECT cr.*
            FROM evals e
            JOIN crawlerrecord cr
                ON e.page_url = cr.page_url
                AND e.school_id = cr.school_id
            LEFT JOIN crawler_records_by_model r
                ON e.page_url = r.page_url
                AND e.school_id = r.school_id
            WHERE r.page_url IS NULL;
            """
            )
            result = session.exec(query)
            pages = result.fetchall()
            pages = [CrawlerRecord.model_validate(row) for row in pages]

        return list(pages)


class TokenLimitExceededException(Exception):
    """Exception raised when the token limit is exceeded."""
    pass


@retry(
    retry=retry_if_not_exception_type(TokenLimitExceededException),
    wait=wait_random_exponential(multiplier=1, min=10, max=300),
    stop=stop_after_attempt(10),
    before_sleep=lambda rcs: print(f"OpenAI call failed: {str(rcs)}"),
    reraise=True
)
def call_openai(openai_client, page: CrawlerRecord, model="gpt-4o-mini", prompt_version="v1"):
    prompt_v1 = f"""
For the web page markdown given to you, extract the following information from it:
- Extract all email addresses as a list. Leave the list empty if there aren't any.
- If the page is a contact page or contact us page, set is_contact_page to True.
- If the page describes a before or after school childcare program, extract those details into before_or_after_care_details.  Otherwise leave it empty.

Follow these rules:
- We ONLY care about before or after care CHILDCARE programs, not general instructions about what students are supposed to do before and after school.  DO NOT include general instructions about what students are supposed to do before and after school.
- DO NOT infer that before or after care is likely and mention that.
- A page is NOT a before or after childcare page if it just links to a page with those deatils.
- DO NOT mention if the page doesn't talk about before or after childcare.

DON'T say things like the following.  These are BAD responses:
- "The page does not provide specific details about before or after school childcare programs"
- "The page provides a link to the Before & After School Programs but does not include specific details about the programs themselves."
- "Students must enter and exit through Door 2. Students must wait patiently in the foyer. Once you exit the building for the day, you will not be allowed back in the building."
- "Plan ahead for before and after school programs."
- "After school programs will run as normal."

A good extraction looks like:
- "Peirce partners with the Lakeview YMCA to offer before and after school care for students in Kindergarten through 8th grades. Programs are run at Peirce School but organized and run by the YMCA. Before care runs from 7:00-8:00 am and after care runs from 3:00 - 6:00 pm."

It's currently the year 2024--DO NOT include information on childcare programs from previous years.

Page URL: {page.page_url}
Page Title: {page.page_title if page.page_title else ""}
Page Description:  {page.description if page.description else ""}
Page Markdown: {page.markdown}
"""
    
    prompt_v2 = f"""
For the web page markdown given to you, extract the following information from it:
- Extract all email addresses as a list. Leave the list empty if there aren't any.
- If the page is a contact page or contact us page, set is_contact_page to True.
- If the page describes a before or after school childcare program, extract those details into before_or_after_care_details.  Otherwise leave it empty.

Follow these rules:
- We ONLY care about before or after care CHILDCARE programs, not general instructions about what students are supposed to do before and after school.  DO NOT include general instructions about what students are supposed to do before and after school.
- DO NOT infer that before or after care is likely and mention that.
- A page is NOT a before or after childcare page if it just links to a page with those deatils.
- DO NOT mention if the page doesn't talk about before or after childcare.
- The abbreviation "OST" stands for "Out of School Time" and should be included.
- Right at School, Park District, and YMCA programs should be included.

DON'T say things like the following.  These are BAD responses:
- "The page does not provide specific details about before or after school childcare programs"
- "The page provides a link to the Before & After School Programs but does not include specific details about the programs themselves."
- "Students must enter and exit through Door 2. Students must wait patiently in the foyer. Once you exit the building for the day, you will not be allowed back in the building."
- "Plan ahead for before and after school programs."
- "After school programs will run as normal."

A good extraction looks like:
- "Peirce partners with the Lakeview YMCA to offer before and after school care for students in Kindergarten through 8th grades. Programs are run at Peirce School but organized and run by the YMCA. Before care runs from 7:00-8:00 am and after care runs from 3:00 - 6:00 pm."
- "We have two after school options - Right At School and Park District."

It's currently the year 2024--DO NOT include information on childcare programs from previous years.

Page URL: {page.page_url}
Page Title: {page.page_title if page.page_title else ""}
Page Description:  {page.description if page.description else ""}
Page Markdown: {page.markdown}
"""
    
    prompt_v3 = f"""
For the web page markdown given to you, extract the following information from it:
- Extract all email addresses as a list. Leave the list empty if there aren't any.
- If the page is a contact page or contact us page, set is_contact_page to True.
- If the page describes a before or after school childcare program, extract those details into before_or_after_care_details.  Otherwise leave it empty.

Follow these rules:
- We ONLY care about before or after care CHILDCARE programs, not general instructions about what students are supposed to do before and after school.  DO NOT include general instructions about what students are supposed to do before and after school.
- DO NOT infer that before or after care is likely and mention that.
- DO NOT mention if the page doesn't talk about before or after childcare.
- If a page mentions that a childcare program starts on a certain date in 2024 or 2025, include it.
- The abbreviation "OST" stands for "Out of School Time" and should be included.
- Extended Day programs should be included.
- Right at School, Park District, and YMCA programs should be included.

DON'T say things like the following.  These are BAD responses:
- "The page does not provide specific details about before or after school childcare programs"
- "The page provides a link to the Before & After School Programs but does not include specific details about the programs themselves."
- "Students must enter and exit through Door 2. Students must wait patiently in the foyer. Once you exit the building for the day, you will not be allowed back in the building."
- "Plan ahead for before and after school programs."
- "After school programs will run as normal."

A good extraction looks like:
- "Peirce partners with the Lakeview YMCA to offer before and after school care for students in Kindergarten through 8th grades. Programs are run at Peirce School but organized and run by the YMCA. Before care runs from 7:00-8:00 am and after care runs from 3:00 - 6:00 pm."
- "We have two after school options - Right At School and Park District."

It's currently the year 2024--DO NOT include information on childcare programs from previous years.

Page URL: {page.page_url}
Page Title: {page.page_title if page.page_title else ""}
Page Description:  {page.description if page.description else ""}
Page Markdown: {page.markdown}
"""

    if prompt_version == "v1":
        prompt = prompt_v1
    elif prompt_version == "v2":
        prompt = prompt_v2
    elif prompt_version == "v3":
        prompt = prompt_v3
    else:
        raise ValueError(f"Invalid prompt version: {prompt_version}")

    tokenizer = tiktoken.encoding_for_model(model)
    n_tokens = len(tokenizer.encode(dedent(prompt)))
    if n_tokens > 100_000:
        raise TokenLimitExceededException(f"Document too long: {n_tokens} tokens")

    completion = openai_client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": "You are an AI expert tasked with understanding elementary and high school websites."},
            {"role": "user", "content": dedent(prompt)} 
        ],
        response_format=CrawlerOpenAIResponse
    )

    response = CrawlerOpenAIResponse.model_validate_json(completion.choices[0].message.content)
    
    record_data = {
        "school_id": page.school_id,
        "school_type": page.school_type,
        "page_url": page.page_url,
        "openai_model_name": model,
        "prompt_version": prompt_version,
        **response.model_dump()
    }

    return CrawlerOpenAIRecord.model_validate(record_data)

client = OpenAI(api_key=os.getenv("CPS_OPENAI_API_KEY"))

MODEL = "gpt-4o-mini" # gpt-4o-2024-08-06
PROMPT_VERSION = "v1"
pages = get_pages(model_name=MODEL, prompt_version=PROMPT_VERSION, evals=False)
random.shuffle(pages)

print(f"Processing {len(pages)} pages...")
for page in pages:
    print(f"Processing {page.page_url}")
    try:
        record = call_openai(client, page, model=MODEL, prompt_version=PROMPT_VERSION)
        with Session(engine) as session:
            session.add(record)
            session.commit()
    except Exception as e:
        print(f"Error processing {page.page_url}: {e}")
        continue
