from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
import chromadb
from llama_index.embeddings.openai import OpenAIEmbedding
import os 
from dotenv import load_dotenv

load_dotenv()

#open persistent client
embed_model = OpenAIEmbedding(model="text-embedding-ada-002") 

documents = SimpleDirectoryReader("./data").load_data()

def create_db_with_indexing(path:str,collection_name:str,embed_model:str,chunk_size:int = 512,chunk_overlap:int =0):
    db = chromadb.PersistentClient(path=path)
    chroma_collection = db.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    service_context = ServiceContext.from_defaults(embed_model=embed_model,chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, service_context=service_context
    )

def load_db_from_disk(path="./chroma_db",collection="YuluQR-enhin-1",embed_model=embed_model):
    db2 = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = db2.get_or_create_collection(collection)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    service_context = ServiceContext.from_defaults(embed_model=embed_model)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        service_context=service_context,
    )
    return index
