# Before Care and After Care at Chicago Public Schools

There does not exist a centralized dataset of before care and after care programs at Chicago Public Schools.  This is a problem for working parents who are trying to make school choice decisions.

This project uses data scraping, web crawling, and LLM's to remedy that problem.

To get the SQLite database itself, first install [git-lfs](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage).


1. `cps_scraper.py` gets a current dataset of all CPS schools and then queries another API to get more information about each school (most importantly its website URL).  This is persisted in a local csv which is then uploaded to an Airtable table.
2. `cps_firecrawl.py` uses the [Firecrawl](https://www.firecrawl.dev/) service to crawl the website of each school.  It uses a SQLModel data model from `cps_firecrawl_models.py` to persist crawled webpage records in a local SQLite database.
3. `cps_openai.py` takes each crawled page and extracts some information from it with gpt-4o-mini.  It pulls out email addresses, whether the page is a contact page, and a string the describes the before and after care program details that may or may not be described on the page.  It uses another SQLModel data model from `cps_firecrawl_models.py` to persist records in the local SQLite database.