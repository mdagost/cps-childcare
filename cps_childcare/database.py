# pyright: reportMissingImports=false
import sqlite_vec
from sqlalchemy import event
from sqlmodel import SQLModel, create_engine

from cps_childcare.cps_data_models import (CrawlerRecord, CrawlerOpenAIRecord,
                                                ChildcareOpenAIRecord, CombinedChildcareOpenAIRecord,
                                                Neighborhood, SchoolToNeighborhood)

sqlite_file_name = "/Users/mdagostino/cps-childcare/data/cps_crawler.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# create the base engine
engine = create_engine(sqlite_url)

# Configure sqlite-vec
def configure_sqlite_vec(dbapi_connection, connection_record):
    dbapi_connection.enable_load_extension(True)
    sqlite_vec.load(dbapi_connection)
    dbapi_connection.enable_load_extension(False)

# import and register the event listener
event.listen(engine, "connect", configure_sqlite_vec)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()
