# Before Care and After Care at Chicago Public Schools

There does not exist a centralized dataset of before care and after care programs at Chicago Public Schools.  This is a problem for working parents who are trying to make school choice decisions.

This project uses data scraping, web crawling, and LLM's to remedy that problem.

If you don't want the ~1 GB SQLite database, clone this repo with `GIT_LFS_SKIP_SMUDGE=1 git clone...`  To get the SQLite database itself, first install [git-lfs](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage) and then, after cloning this repo, run `git lfs pull`.

## Installation

1. Create a virtualenv for python >=3.10.
2. Run poetry install.
3. If you want to reproduce all of this yourself, make sure you have the following API keys set as environment variables:
    - Airtable API key at `AIRTABLE_API_KEY`
    - Firecrawl API key at `FIRECRAWL_API_KEY`
    - OpenAI API key at `OPENAI_API_KEY`

These are the scripts to run:

1. `cps_scraper.py` gets a current dataset of all CPS schools and then queries another API to get more information about each school (most importantly its website URL).  This is persisted in a local csv which is then uploaded to an Airtable table.
2. `cps_firecrawl.py` uses the [Firecrawl](https://www.firecrawl.dev/) service to crawl the website of each school.  It uses a SQLModel data model from `cps_firecrawl_models.py` to persist crawled webpage records in a local SQLite database.
3. `cps_openai.py` takes each crawled page and extracts some information from it with gpt-4o-mini.  It pulls out email addresses, whether the page is a contact page, and a string the describes the before and after care program details that may or may not be described on the page.  It uses another SQLModel data model from `cps_firecrawl_models.py` to persist records in the local SQLite database.