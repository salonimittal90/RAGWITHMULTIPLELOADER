from langchain_community.document_loaders import WebBaseLoader,PyPDFLoader,Docx2txtLoader, UnstructuredPowerPointLoader, GitLoader,UnstructuredFileLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter,CharacterTextSplitter
from config import vector_store 
import os 
from dotenv import load_dotenv
import hashlib
import time
import ssl
load_dotenv()

ssl._create_default_https_context = ssl._create_unverified_context
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["UNSTRUCTURED_OFFLINE"] = "1"

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests
requests.packages.urllib3.disable_warnings()

# More SSL bypass
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Requests session with no SSL verification
import requests
session = requests.Session()
session.verify = False


def load_and_index_documents(source,source_type):
    if source_type == "web":
        loader = WebBaseLoader(
            web_paths=(source,),
            requests_kwargs={"verify": False},
        )
    elif source_type == "pdf":
        loader = PyPDFLoader(source)
    
    elif source_type == "docx":
         loader = Docx2txtLoader(source)

    elif source_type == "csv":
        loader = CSVLoader(source)

    elif source_type == "pptx":
        loader = UnstructuredPowerPointLoader(source)
    
    # elif source_type == "git":
    #     username = os.getenv("GIT_USERNAME")
    #     password = os.getenv("GIT_PASSWORD")
    
    #     clean_url = source.replace("https://saloniamittal@", "https://")
    
    #     if username and password:
    #         auth_url = clean_url.replace("https://", f"https://{username}:{password}@")
    #     else:
    #         auth_url = clean_url

    #     timestamp = str(int(time.time()))
    #     url_hash = hashlib.md5(clean_url.encode()).hexdigest()[:6]
    #     unique_path = f"C:/Users/salmitta/Desktop/repo_{url_hash}_{timestamp}"

    #     loader = GitLoader(
    #         clone_url=auth_url,
    #         repo_path=unique_path,
    #         branch="master",
    #         file_filter=lambda file_path: file_path.endswith(('.py', '.js', '.md', '.txt'))
    #     )
    
    # elif source_type == "image" or source_type in ["jpg", "jpeg", "png", "gif", "bmp"]:
    #     loader = UnstructuredFileLoader(source)


    else:
        raise ValueError(f"Unsupported source_type: {source_type}")
    


    docs = loader.load()
    print(f"Loaded {len(docs)} documents from {source_type}")
    # print
    if docs:
        print(f"First document content preview:")
        print(f"Page content: {docs[0].page_content}...")
        print(f"Document metadata: {docs[0].metadata}")


    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)
    print(f"\n=== RecursiveCharacterTextSplitter Results ===")
    print(f"Split {len(docs)} documents into {len(all_splits)} chunks")
    for i, chunk in enumerate(all_splits[:3]):  # First 3 chunks only
        print(f"\nChunk {i+1}:")
        print(f"Content: {chunk.page_content[:200]}...")
        print(f"Length: {len(chunk.page_content)} characters")


    # text_splitter = CharacterTextSplitter(separator = ".", keep_separator=True,  chunk_size=1000)
    # all_splits2 = text_splitter.split_documents(docs)
    # print(f"\n=== CharacterTextSplitter Results ===")
    # print(f"Split {len(docs)} documents into {len(all_splits2)} chunks")
    # for i, chunk in enumerate(all_splits2[:3]):  # First 3 chunks only
    #     print(f"\nChunk {i+1}:")
    #     print(f"Content: {chunk.page_content[:200]}...")
    #     print(f"Length: {len(chunk.page_content)} characters")

    _ = vector_store.add_documents(documents=all_splits)
    return len(all_splits)

