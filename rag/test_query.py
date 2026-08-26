import chromadb
from chromadb.utils import embedding_functions

# Explicitly use the same embedding function ("all-MiniLM-L6-v2")
embedding_function = embedding_functions.DefaultEmbeddingFunction()

chroma_client = chromadb.PersistentClient(path="rag/chroma_db")
collection = chroma_client.get_collection(
    name="orientia_knowledge",
    embedding_function=embedding_function
)

query = "Quelles sont les matières en informatiques ?"

results = collection.query(
    query_texts=[query],
    n_results=2
)

print(f"Question : {query}\n")
for i in range(len(results['documents'][0])):
    doc = results['documents'][0][i]
    meta = results['metadatas'][0][i]
    print(f"--- Résultat {i+1} ---")
    print(f"Source originale : {meta['original_file']} (ID: {meta['source_id']})")
    print(f"Titre : {meta['title']}")
    if 'Header 2' in meta:
        print(f"Section : {meta['Header 2']}")
    print(f"Extrait : \n{doc}\n")
