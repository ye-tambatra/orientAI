import chromadb
from chromadb.utils import embedding_functions

# Initialize the embedding function using the "all-MiniLM-L6-v2" model (downloads automatically to ~/.cache/chroma on first run)
embedding_function = embedding_functions.DefaultEmbeddingFunction()

# Initialize ChromaDB client pointing to our local storage
chroma_client = chromadb.PersistentClient(path="rag/chroma_db")

# Load the existing collection
collection = chroma_client.get_collection(
    name="orientia_knowledge", 
    embedding_function=embedding_function
)

def retrieve_context(query: str, n_results: int = 3) -> str:
    """
    Queries ChromaDB and returns a formatted context string.
    This string is meant to be directly injected into an LLM prompt.
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    context_blocks = []
    
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        
        # Extract section header if it exists (useful for context hierarchy)
        section = meta.get('Header 2', meta.get('Header 1', 'General Section'))
        
        # Format the context block with source information for citation purposes
        block = (
            f"[Source: {meta['original_file']}, ID: {meta['source_id']}]\n"
            f"Title: {meta['title']} ({section})\n"
            f"Content:\n{doc}\n"
        )
        context_blocks.append(block)
        
    return "\n---\n\n".join(context_blocks)

if __name__ == "__main__":
    # Example usage for testing the retrieval function
    test_query = "What are the subjects for BIO 1?"
    print(f"Retrieving context for: '{test_query}'\n")
    print(retrieve_context(test_query))
