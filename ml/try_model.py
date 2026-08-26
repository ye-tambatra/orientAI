"""Manual test REPL for the ML model ALONE — no LLM, no GEMINI_API_KEY needed.

Lets you type a profile in free text (matières, intérêts, compétences) and
see exactly what ml/inference.py returns: the ranked domains, their score,
the looked-up ISPM filières, and the "points forts" explanation. Useful to
sanity-check the model without going through the conversational agent.

Run from the repo root with:
    python -m ml.try_model

Requires a trained model — run `python -m ml.train` first if
ml/artifacts/model.json does not exist yet.
"""

from ml.inference import ModelNotTrainedError, get_model


def ask(prompt: str) -> list[str]:
    raw = input(prompt).strip()
    return [item.strip() for item in raw.split(",") if item.strip()]


if __name__ == "__main__":
    try:
        model = get_model()
    except ModelNotTrainedError as e:
        print(f"Erreur : {e}")
        raise SystemExit(1)

    print("Test manuel du modèle ML ORIENT'IA (Ctrl+C pour quitter).")
    print("Réponds avec une liste séparée par des virgules, ou appuie sur Entrée pour laisser vide.\n")

    while True:
        try:
            matieres = ask("Matières préférées : ")
            competences = ask("Compétences déclarées : ")
            interets = ask("Centres d'intérêt : ")
        except (KeyboardInterrupt, EOFError):
            print("\nÀ bientôt.")
            break

        profile = {
            "matieres_preferees": matieres,
            "competences": competences,
            "centres_interet": interets,
        }

        ranking = model.rank_domaines(profile, k=5)
        if not ranking:
            print("\n-> Rien d'exploitable dans ce profil (aucun tag reconnu).\n")
            continue

        print("\nClassement des domaines :")
        for i, r in enumerate(ranking, start=1):
            filieres = ", ".join(r["filieres_ispm_correspondantes"]) or "aucune"
            print(f"  {i}. {r['label']:55s} score={r['score']:.3f}  filières ISPM: {filieres}")

        points = model.points_forts(profile)
        print(f"\nPoints forts identifiés : {', '.join(points) if points else '(aucun)'}")
        print("-" * 70 + "\n")
