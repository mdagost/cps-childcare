import re

import lancedb
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.schema import MetadataMode,TransformComponent
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import MarkdownNodeParser, MarkdownElementNodeParser, SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
from llama_index.vector_stores.lancedb import LanceDBVectorStore
from sqlmodel import Session, select, text

from cps_childcare.database import engine
from cps_childcare.cps_data_models import CrawlerRecord, WebPageChunk


class EmbeddedImageCleaner(TransformComponent):
    def __call__(self, nodes, **kwargs):
        for node in nodes:
            node.text = re.sub(r'data:image/([^;]*);base64,[^"]*', r'data:image/\1;base64)', node.text)
        return nodes


class HeaderPathCleaner(TransformComponent):
    max_header_length: int = 100

    def __init__(self, max_header_length=10):
        super().__init__()
        self.max_header_length = max_header_length

    def __call__(self, nodes, **kwargs):
        for node in nodes:
            header_path = node.metadata.get("header_path", "")
            if len(header_path) > self.max_header_length:
                node.metadata["header_path"] = header_path[:self.max_header_length]
        return nodes


def clean_page_title(page_title):
    if page_title:
        return re.sub(r'<!\[CDATA\[.*?\]>', r'', page_title)
    else:
        return None


if __name__ == "__main__":
    VECTOR_DB_URI = "data/embeddings.lancedb"
    TABLE_NAME = "webpagechunk"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 100
    EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5" # "BAAI/bge-en-icl"
    
    vector_store = LanceDBVectorStore( 
        uri=VECTOR_DB_URI,
        table_name=TABLE_NAME,
        mode="overwrite" # append
    )

    vector_db = lancedb.connect(VECTOR_DB_URI)
    if TABLE_NAME not in vector_db.table_names():
        table = vector_db.create_table(TABLE_NAME, schema=WebPageChunk)
    else:
        table = vector_db.open_table(TABLE_NAME)

    local_embedding_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL,trust_remote_code=True)

    gpu_embedding_model = TextEmbeddingsInference(
        model_name=EMBEDDING_MODEL,
        base_url="http://54.173.78.188:8080",
        auth_token="Bearer cpschildcare",
        timeout=60,  # in seconds
        embed_batch_size=32 # this is the max allowed by the server
    )

    pipeline = IngestionPipeline(
        transformations=[
            EmbeddedImageCleaner(),
            MarkdownNodeParser(),
            HeaderPathCleaner(max_header_length=CHUNK_SIZE // 3),
            SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP),
            gpu_embedding_model
        ],
        vector_store=vector_store
    )

    with Session(engine) as session:
        pages= session.exec(
            select(CrawlerRecord)
            .where(CrawlerRecord.status_code == 200)
            .where(CrawlerRecord.markdown != None)
            .order_by(CrawlerRecord.id)
        ).all()

        docs = [Document(
                text=page.markdown,
                metadata={
                    "school_name": page.school_name.title(),
                    "page_url": page.page_url,
                    "page_title": clean_page_title(page.page_title),
                }
            ) for page in pages
        ]

        nodes = pipeline.run(documents=docs, show_progress=True, num_workers=None)






        # for page_num, page in enumerate(pages):
        #     # create a Document object with metadata
        #     doc = Document(
        #         text=page.markdown,
        #         metadata={
        #             "school_id": page.school_id,
        #             "page_url": page.page_url,
        #             "page_title": page.page_title,
        #             "description": page.description
        #         }
        #     )

        #     nodes = pipeline.run(documents=[doc])

        #     for node in nodes:
        #         #print(node.node_id)
        #         #print(node.text)
        #         #print(node.metadata)
        #         #print(node.to_dict())
        #         print("".join(["-"]*50))

        #         chunk_dict = {
        #             "id": node.node_id,
        #             "school_id": node.metadata["school_id"],
        #             "page_url": node.metadata["page_url"],
        #             "chunk_text": node.text,
        #             "chunk_embedding": node.embedding
        #         }
                
        #         chunk = WebPageChunk.model_validate(chunk_dict)
                
        #         table.add([chunk])

        #     if page_num > 10:
        #         break
