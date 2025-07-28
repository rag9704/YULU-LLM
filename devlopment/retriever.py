from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import BaseRetriever
from indexing import load_db_from_disk,embed_model


class HybridRetriever(BaseRetriever):
    def __init__(self, vector_retriever, bm25_retriever):
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        super().__init__()

    def _retrieve(self, query, **kwargs):
        bm25_nodes = self.bm25_retriever.retrieve(query, **kwargs)
        vector_nodes = self.vector_retriever.retrieve(query, **kwargs)

        # combine the two lists of nodes
        all_nodes = []
        node_ids = set()
        for n in bm25_nodes + vector_nodes:
            if n.node.node_id not in node_ids:
                all_nodes.append(n)
                node_ids.add(n.node.node_id)
        return all_nodes
    
class YuluHybridRetriever:
    def __init__(self, path="./chroma_db", collection="YuluQR-enhin-1", embed_model=embed_model):
        self.index = load_db_from_disk(path=path, collection=collection, embed_model=embed_model)
        self.documents = SimpleDirectoryReader(
            input_files=["/home/data/llm/deployment/data/yulu_quickride.txt"]
        ).load_data()
        self.splitter = SentenceSplitter(chunk_size=200, chunk_overlap=10)
        self.nodes = self.splitter.get_nodes_from_documents(self.documents)
        self.bm25_retriever = BM25Retriever.from_defaults(nodes=self.nodes, similarity_top_k=2)
        self.vector_retriever = self.index.as_retriever(similarity_top_k=5)
        self.hybrid_retriever = HybridRetriever(self.vector_retriever, self.bm25_retriever)

    @property
    def hybrid_retriever_instance(self):
        return self.hybrid_retriever
    
    def retrieve(self, query, **kwargs):
        return self.hybrid_retriever.retrieve(query, **kwargs)

# Usage
