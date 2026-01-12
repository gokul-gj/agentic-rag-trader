import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Define paths
DATA_DIR = os.path.join(os.getcwd(), 'data')
DB_DIR = os.path.join(os.getcwd(), 'chroma_db')

# Initialize Embedding Function (Local/Offline by default)
embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def ingest_documents():
    """Reads PDFs from data folder and stores them in ChromaDB."""
    documents = []
    
    # Check if data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created {DATA_DIR}. Please place PDFs there.")
        return

    # Load PDFs
    for file in os.listdir(DATA_DIR):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(DATA_DIR, file)
            print(f"Loading {file}...")
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())

    if not documents:
        print("No documents found to ingest.")
        return

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)

    # Store in Chroma
    print(f"Storing {len(chunks)} chunks in ChromaDB...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=DB_DIR
    )
    print("Ingestion Complete.")

def add_texts(texts: List[str], metadatas: List[dict] = None):
    """Adds raw text data (e.g. news) to the vector store."""
    if not texts:
        return
        
    print(f"Adding {len(texts)} text entries to ChromaDB...")
    vector_store = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embedding_function
    )
    vector_store.add_texts(texts=texts, metadatas=metadatas)
    print("Texts Added.")

def query_strategy_rules(topic: str, k: int = 3) -> List[str]:
    """Retrieves top k relevant chunks for a given topic."""
    
    # Connect to existing DB
    if not os.path.exists(DB_DIR):
        print("Database not found. Please run ingestion first.")
        return []

    vector_store = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embedding_function
    )

    print(f"Querying for: {topic}")
    results = vector_store.similarity_search(topic, k=k)
    return [doc.page_content for doc in results]

if __name__ == "__main__":
    # For testing purposes
    # ingest_documents()
    # print(query_strategy_rules("short strangle entry"))
    pass
