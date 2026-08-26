import json

with open("data/structured/sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

sources.append({
    "id": "SRC005",
    "title": "Informations générales sur l'ISPM",
    "type": "md",
    "file": "data/structured/informations_ispm.md",
    "url": "https://ispm-edu.com/presentation.php",
    "status": "official",
    "consulted_at": "2026-08-26",
    "description": "Informations de contact et horaires de l'ISPM",
    "extracted_data": ["contact", "adresse"],
    "limitations": None
})

with open("data/structured/sources.json", "w", encoding="utf-8") as f:
    json.dump(sources, f, indent=2, ensure_ascii=False)
