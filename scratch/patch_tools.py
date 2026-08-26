import re

with open("llm/tools.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace the specific duplicate block
bad_block = '''def comparer_parcours(filiere_a: str, filiere_b: str) -> str:
    """Compare deux filières/parcours de l'ISPM entre elles.

    Utilise ceci quand l'utilisateur hésite entre deux filières et veut les
    comparer.

    Args:
        filiere_a: Le nom ou sigle de la première filière.
        filiere_b: Le nom ou sigle de la deuxième filière.
    """
    query = f"Différence et comparaison entre la filière {filiere_a} et {filiere_b}"
    return retrieve_context(query, n_results=15)'''

content = content.replace(bad_block, "")
# remove empty lines
content = re.sub(r'\n{3,}', '\n\n', content)

with open("llm/tools.py", "w", encoding="utf-8") as f:
    f.write(content)
