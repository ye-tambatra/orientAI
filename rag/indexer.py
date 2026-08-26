import json
import os
import glob
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import MarkdownHeaderTextSplitter

# Explicitly specify the embedding model. By default, ChromaDB uses "all-MiniLM-L6-v2".
# ChromaDB downloads this model automatically to ~/.cache/chroma/onnx_models/
embedding_function = embedding_functions.DefaultEmbeddingFunction()

# 1. Load Sources Metadata
with open('data/structured/sources.json', 'r', encoding='utf-8') as f:
    sources = json.load(f)

def get_source_meta(md_file):
    base = os.path.basename(md_file).replace('.md', '')
    for s in sources:
        if base in s['file']:
            return s
        if base == 'lectures_list' and s['type'] == 'pdf':
            return s
    return None

# 2. Init Langchain Markdown Splitter
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

# 3. Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="rag/chroma_db")
try:
    chroma_client.delete_collection(name="orientia_knowledge")
except:
    pass

# We pass the embedding function explicitly here
collection = chroma_client.create_collection(
    name="orientia_knowledge",
    embedding_function=embedding_function
)

# 4. Process and Index Data
md_files = glob.glob('data/structured/*.md')
for md_file in md_files:
    meta = get_source_meta(md_file)
    if not meta:
        continue
        
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    md_header_splits = markdown_splitter.split_text(content)
    
    for i, doc in enumerate(md_header_splits):
        chunk_meta = {
            "source_id": meta['id'],
            "original_file": meta['file'],
            "title": meta['title']
        }
        for key, value in doc.metadata.items():
            chunk_meta[key] = value
            
        chunk_id = f"{meta['id']}_chunk_{i}"
        
        collection.add(
            documents=[doc.page_content],
            metadatas=[chunk_meta],
            ids=[chunk_id]
        )
    print(f"Indexed {len(md_header_splits)} chunks from {meta['file']}")

print(f"Indexation terminée. Base ChromaDB mise à jour dans 'rag/chroma_db/'.")
