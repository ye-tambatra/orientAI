"""Calcule une proximité structurelle entre filières (tronc commun de
matières), pour éclairer la question des "passerelles entre formations"
(sujet, section 3) sans jamais prétendre qu'une passerelle officielle existe.

Pourquoi ce n'est PAS la même situation que compétences/métiers
------------------------------------------------------------------
Pour les compétences (derive_competences.py) et les métiers
(derive_relations.py), dériver une inférence générique était défendable :
"telle matière développe telle compétence" est une observation
pédagogique générale, indépendante de la politique interne de l'ISPM.

Une PASSERELLE est différente : c'est une AUTORISATION ADMINISTRATIVE réelle
("un étudiant de X peut intégrer Y en 2e année"). Le fait que deux filières
partagent un tronc commun de matières en première année NE PROUVE PAS qu'un
tel transfert est autorisé — ce serait une invention de règle d'admission,
explicitement interdite par le sujet (section 4 : "Une information non
vérifiée ne devra pas être présentée comme une information officielle" ;
section 16 : "confusion entre conseil pédagogique et décision
administrative").

Vérifié le 27/08/2026 (WebFetch sur ispm-edu.com/inscription.php et
/filieres.php) : aucune passerelle n'est mentionnée sur le site officiel.

Ce script calcule donc uniquement un fait descriptif et vérifiable dans NOS
PROPRES données (le nombre de matières communes entre deux filières,
d'après data/structured/lectures_list.md), présenté comme une simple
proximité de programme — jamais comme une passerelle confirmée. Le fichier
généré et l'outil qui l'utilise (llm/tools.py) redirigent systématiquement
vers l'administration ISPM pour toute confirmation réelle.

Reproductibilité : `python -m data_processing.derive_proximite_filieres`
régénère `data/structured/proximite_filieres.md` à partir de
`ml/filieres.py` (aucune dépendance réseau).
"""

from __future__ import annotations

from ml.filieres import FILIERES

OUTPUT_MD = "data/structured/proximite_filieres.md"

TOP_N = 3


def matieres_communes(code_a: str, code_b: str) -> list[str]:
    a = set(FILIERES[code_a].matieres)
    b = set(FILIERES[code_b].matieres)
    return sorted(a & b)


def filieres_proches(code: str, top_n: int = TOP_N) -> list[tuple[str, list[str]]]:
    """Renvoie les `top_n` autres filières ayant le plus de matières en
    commun avec `code`, avec la liste des matières partagées (transparence :
    jamais un score opaque, toujours les faits derrière).
    """
    scored = []
    for other_code in FILIERES:
        if other_code == code:
            continue
        communes = matieres_communes(code, other_code)
        if communes:
            scored.append((other_code, communes))
    scored.sort(key=lambda item: len(item[1]), reverse=True)
    return scored[:top_n]


def main() -> None:
    lines = [
        "# Proximité structurelle entre filières (tronc commun de matières)",
        "",
        "> **CECI N'EST PAS UNE PASSERELLE OFFICIELLE.** Aucune passerelle "
        "entre filières n'est mentionnée sur le site officiel de l'ISPM "
        "(vérifié le 27/08/2026 sur ispm-edu.com/inscription.php et "
        "/filieres.php). Ce document liste uniquement, à titre informatif, "
        "les matières de première année que deux filières ont en commun "
        "— un fait descriptif calculé à partir de "
        "`data/structured/lectures_list.md`, PAS une autorisation de "
        "transfert. Un tronc commun important ne signifie pas qu'un "
        "changement de filière soit possible ou autorisé. **Toute question "
        "de réorientation ou de passerelle réelle doit être posée à "
        "l'administration de l'ISPM.**",
        "",
    ]
    for code, filiere in FILIERES.items():
        proches = filieres_proches(code)
        lines.append(f"## {filiere.nom} ({code})")
        lines.append("")
        if not proches:
            lines.append(
                "Aucune autre filière ne partage de matière de première "
                "année dans nos données (ne signifie pas qu'aucune "
                "passerelle n'existe — se renseigner auprès de "
                "l'administration)."
            )
        else:
            lines.append(
                "**Filières avec le tronc commun le plus important "
                "(informatif, PAS une passerelle confirmée) :**"
            )
            lines.append("")
            for other_code, communes in proches:
                other_nom = FILIERES[other_code].nom
                lines.append(
                    f"- {other_nom} ({other_code}) — {len(communes)} "
                    f"matière(s) commune(s) : {', '.join(communes)}"
                )
        lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Calcul terminé. Résultats dans {OUTPUT_MD}")


if __name__ == "__main__":
    main()
