from __future__ import annotations
import chromadb
from sentence_transformers import SentenceTransformer
import glob
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logfire
from util import Util
from pathlib import Path
from pypdf import PdfReader

EMPTY_STRING = ""
# Initialize ChromaDB and model
client = chromadb.PersistentClient(path=Path(__file__).resolve().parent.parent.joinpath('chroma'))
collection = client.get_or_create_collection("knowledge-docs")

def read_docs(path: str):
    # Read content from the input file path or from content from all the file from the input folder path
    docs = []
    doc_paths = []
    if path.endswith(".pdf"):
        final_path = path
    else:
        final_path = path + "/*.pdf"
    files = glob.glob(final_path, recursive=True)
    files_count = len(files)
    if files_count == 0:
        raise FileNotFoundError(Util.FILE_NOT_FOUND_ERROR)
    for file_path in files:
        reader = PdfReader(str(file_path))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text() or ""
            text += extracted + "\n"
        content = text.strip()
        if content:  # Only add non-empty files
            docs.append(content)
            doc_paths.append(file_path)
    return docs, doc_paths


@logfire.instrument("RagService.get_ingested_data")
def get_ingested_data(user_input:str) -> str:
    # Verify storage
    count = collection.count()
    print(f"   ✅ Vector database contains {count} documents")
    if count == 0:
        return EMPTY_STRING
    results = collection.query(
        query_texts=[user_input],
        n_results=3
    )
    context_docs = ""
    for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
        similarity = 1 - distance
        context_docs += doc
    if len(context_docs) > 0:
        return context_docs
    else:
        return EMPTY_STRING

@logfire.instrument("RagService.delete_ingested_data")
def delete_ingested_data() -> None:
    print("delete_ingested_data")
    client.delete_collection("knowledge-docs")
    global collection
    collection = client.get_or_create_collection("knowledge-docs")

@logfire.instrument("RagService.ingest_data_from_file_or_folder")
def ingest_data_from_file_or_folder(path: str) -> None:
    print("ingest_data_from_file_or_folder")
    docs, doc_paths = read_docs(path)
    # Split document into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    total_chunks = 0
    all_chunk_ids = []
    all_embeddings = []
    for doc_index, doc in enumerate(docs):
        chunks = splitter.split_text(doc)

        # Generate chunk IDs
        chunk_ids = [f"chunk_{total_chunks + i + 1}" for i in range(len(chunks))]

        # Create embeddings for all documents
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(chunks).tolist()

        # Add documents to ChromaDB
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=[{"source_doc": f"doc_{doc_index + 1}"} for _ in chunks]
        )
        total_chunks += len(chunk_ids)
        all_chunk_ids.extend(chunk_ids)
        all_embeddings.extend(embeddings)