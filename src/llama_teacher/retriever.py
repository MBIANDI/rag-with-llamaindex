import os

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.llms.openai import OpenAI

from llama_teacher.prompt import SYSTEM_PROMPT
from src.config import settings


class ChatEngineManager:
    def __init__(self):
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        self.llm = OpenAI(
            model=settings.openai_model_name,
            temperature=settings.temperature,
            api_key=settings.openai_api_key,
        )
        self.index = self._get_or_create_index()

    def _get_or_create_index(self):
        # Vérifie si l'index existe déjà sur le disque (dans chroma_db défini dans config)
        if settings.db_dir.exists() and any(settings.db_dir.iterdir()):
            storage_context = StorageContext.from_defaults(
                persist_dir=str(settings.db_dir)
            )
            return load_index_from_storage(storage_context)
        else:
            # Sinon, on lit les docs et on crée l'index
            documents = SimpleDirectoryReader(str(settings.dat_dir)).load_data()
            index = VectorStoreIndex.from_documents(documents)
            index.storage_context.persist(persist_dir=str(settings.db_dir))
            return index

    def get_retriever(self):
        return QueryFusionRetriever(
            [self.index.as_retriever(similarity_top_k=settings.chunk_size)],
            llm=self.llm,
            similarity_top_k=settings.top_k_fusion,
            num_queries=settings.num_queries,
            mode="reciprocal_rerank",
            use_async=True,
        )

    def get_chat_engine(self):
        retriever = self.get_retriever()
        return ContextChatEngine.from_defaults(
            retriever=retriever,
            system_prompt=SYSTEM_PROMPT,
            streaming=True,
            verbose=True,  # Utile pour voir les requêtes générées par la fusion dans la console
        )
