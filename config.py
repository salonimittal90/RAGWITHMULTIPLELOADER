import os
from pymongo import MongoClient, AsyncMongoClient
from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch

# Load .env file
load_dotenv()

class Settings:
    """Configuration class that loads all environment variables"""
    def __init__(self):
        # MongoDB Configuration
        self.MONGO_URI = os.getenv('MONGO_URI')
        self.DATABASE_NAME = os.getenv('DATABASE_NAME')

        # Ollama Configuration
        self.OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
        self.OLLAMA_EMBEDDING_MODEL = os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')

        # Vector Search Configuration
        self.VECTOR_INDEX = os.getenv('VECTOR_INDEX')
        self.RAG_COLLECTION = os.getenv('RAG_COLLECTION', 'RAG')

# Create settings instance
settings = Settings()

# Create synchronous MongoDB client for vector store
client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]
collection = db[settings.RAG_COLLECTION]

# Create an asynchronous MongoDB client to interact with the database for checkpointers
aclient = AsyncMongoClient(settings.MONGO_URI)

# Initialize Ollama embeddings
embeddings = OllamaEmbeddings(
    model=settings.OLLAMA_EMBEDDING_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
)

# Initialize vector store with Ollama embeddings
vector_store = MongoDBAtlasVectorSearch(
    collection=collection,
    embedding=embeddings,
    index_name=settings.VECTOR_INDEX,
)

# Initialize Ollama LLM with qwen3:4b model
llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0.7,
)

