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
        section = meta.get('Header 3') or meta.get('Header 2') or meta.get('Header 1') or 'General Section'
        
        # Format the context block with source information for citation purposes
        block = (
            f"[Source: {meta['original_file']}, ID: {meta['source_id']}]\n"
            f"Title: {meta['title']} ({section})\n"
            f"Content:\n{doc}\n"
        )
        context_blocks.append(block)
        
    return "\n---\n\n".join(context_blocks)


def retrieve_by_keyword(keyword: str, n_results: int = 4) -> str:
    """
    Recherche par correspondance textuelle exacte (insensible à la casse) du
    mot-clé dans le contenu des chunks, plutôt que par similarité vectorielle.

    Pourquoi : la recherche vectorielle par défaut (all-MiniLM-L6-v2 sur un
    corpus francophone très hétérogène) échoue régulièrement à faire remonter
    le chunk le plus évident pour une entité connue (ex: interroger sur
    "ISAIA" ne classe pas forcément le chunk ISAIA dans les premiers
    résultats — vérifié). Quand l'appelant connaît un identifiant précis
    (sigle de filière, code), une recherche par mot-clé est plus fiable
    qu'une recherche sémantique. Utilisée en complément de
    `retrieve_context`, pas en remplacement (elle ne comprend pas les
    reformulations libres).

    Args:
        keyword: Le mot-clé à chercher tel quel dans le contenu des chunks
            (ex: un sigle de filière comme "ISAIA").
        n_results: Nombre maximum de chunks correspondants à renvoyer.
    """
    all_docs = collection.get(include=["documents", "metadatas"])
    keyword_lower = keyword.lower()

    scored = []
    for doc, meta in zip(all_docs["documents"], all_docs["metadatas"]):
        header = str(meta.get("Header 3") or meta.get("Header 2") or meta.get("Header 1") or "")
        header_match = keyword_lower in header.lower()
        content_hits = doc.lower().count(keyword_lower)
        if not header_match and not content_hits:
            continue
        # Un chunk dont le TITRE DE SECTION correspond (ex: "... (ISAIA)")
        # est presque toujours le bon résultat : une grande page de menu qui
        # mentionne juste le sigle une fois dans une liste ne doit pas
        # passer devant. D'où l'écart de score volontairement large.
        score = (100 if header_match else 0) + content_hits
        scored.append((score, doc, meta))

    scored.sort(key=lambda item: item[0], reverse=True)
    matches = [(doc, meta) for _, doc, meta in scored]

    if not matches:
        return ""

    context_blocks = []
    for doc, meta in matches[:n_results]:
        section = meta.get('Header 3') or meta.get('Header 2') or meta.get('Header 1') or 'General Section'
        block = (
            f"[Source: {meta['original_file']}, ID: {meta['source_id']}]\n"
            f"Title: {meta['title']} ({section})\n"
            f"Content:\n{doc}\n"
        )
        context_blocks.append(block)

    return "\n---\n\n".join(context_blocks)


def retrieve_context_for_entity(entity: str, query: str, n_results: int = 4) -> str:
    """
    Combine recherche par mot-clé (priorité) et recherche vectorielle
    (complément), pour un appelant qui connaît une entité précise (ex: un
    sigle de filière) en plus d'une requête en langage naturel.

    Args:
        entity: Identifiant précis à rechercher d'abord par correspondance
            textuelle (ex: "ISAIA").
        query: Requête en langage naturel pour la recherche vectorielle,
            utilisée en complément (et en fallback si `entity` ne trouve
            rien).
        n_results: Nombre de chunks à renvoyer au total.
    """
    keyword_result = retrieve_by_keyword(entity, n_results=n_results)
    if not keyword_result:
        return retrieve_context(query, n_results=n_results)

    # Complète avec la recherche vectorielle si peu de chunks trouvés par
    # mot-clé, pour ne pas priver le LLM de contexte utile (ex: passages
    # génériques sur les compétences/matières qui ne citent pas le sigle
    # littéralement).
    keyword_count = keyword_result.count("[Source:")
    if keyword_count >= n_results:
        return keyword_result

    vector_result = retrieve_context(query, n_results=n_results - keyword_count)
    return f"{keyword_result}\n---\n\n{vector_result}"


if __name__ == "__main__":
    # Example usage for testing the retrieval function
    test_query = "What are the subjects for BIO 1?"
    print(f"Retrieving context for: '{test_query}'\n")
    print(retrieve_context(test_query))
