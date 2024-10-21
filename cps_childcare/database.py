# pyright: reportMissingImports=false
from sqlmodel import SQLModel, create_engine

from cps_firecrawl_models import CrawlerRecord, CrawlerOpenAIRecord

sqlite_file_name = "/Users/mdagostino/cps-childcare/data/cps_crawler.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()
