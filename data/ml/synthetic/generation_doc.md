# Génération des données synthétiques ORIENT'IA

Documented synthetic profile generator (training data).

Per the brief's section 5 warning ("Un jeu entièrement synthétique est
engendré à partir de règles : le modèle qui l'apprend ne fait que
retrouver ces règles"), this generator deliberately injects noise and
label ambiguity rather than emitting profiles that perfectly match a
domain's textbook definition. It is not meant to be a source of truth by
itself — it is meant to be generalised *away from*, which is measured by
testing the trained model on the real survey responses (ml/survey.py).

The model's label space is a set of general pedagogical/professional
orientation **domains** (ml.domaines), not ISPM filière codes — see
ml/domaines.py's module docstring for why.

Method (documented, as required by section 5)
-----------------------------------------------
For each of the 15 orientation domains:
1. Build a pool of "candidate tags" from ml.vocab using the hand-curated
   domain/tag affinity weights (>= 0.5 = strong match, 0.3-0.5 = weak/
   plausible match).
2. Sample 2-4 "matières préférées" and 1-3 "centres d'intérêt" tags,
   weighted by affinity, mixing in the occasional out-of-domain tag.
3. Sample "compétences déclarées" from the *same* domain-tag pool at a
   lower rate — deliberately NOT from any personality/character trait
   vocabulary, since section 16 of the brief forbids using inferred
   personality/character as a recommendation criterion. This exclusion is
   a design decision, not an oversight.
4. Sample environnement_travail = the domain's dominant environment with
   probability 0.75, a random other environment otherwise (self-report
   noise: people are imperfect judges of their environment preference).
5. Sample serie_bac from a coarse, hand-set distribution per broad
   category (scientific/technical domains skew towards S/D/C; business/
   law/tourism domains skew towards A/D/L) — this is a HYPOTHESIS about
   Malagasy secondary-school streaming, not a verified statistic.
6. With probability P_MISLABEL, the row's features are generated for
   domain X but the recorded label is a *different* domain Y that shares
   at least one tag with X — simulating the real phenomenon (documented
   in the brief) that a student's actual past choice is not always the
   choice that best fit their profile. These rows are flagged
   `label_noise=True` in the exported CSV so any downstream analysis can
   isolate their effect.

Biases potentially introduced (documented, as required by section 5)
----------------------------------------------------------------------
- The tag/domain affinity weights are hand-curated (ml.vocab), not
  learned from data — they encode the generator's own assumptions about
  which subjects "belong" to which domain, so a model trained purely on
  this data risks re-learning the generator's biases rather than a
  genuine population's.
- Classes are perfectly balanced (equal profiles per domain), which does
  not reflect real applicant volumes across fields of study.
- No demographic attribute (gender, age, origin) is generated or used at
  all, by design (section 16 forbids using such attributes as
  recommendation criteria).

Consistency controls applied
------------------------------
- Every generated profile has at least one non-empty field.
- `label_noise` rows are capped at P_MISLABEL (default 6%) and clearly
  flagged rather than silently mixed in.
- The tag pool, sampling probabilities and this documentation live in one
  file so the generation process is reproducible from a fixed `seed`.


## Paramètres effectivement utilisés pour cette version du jeu de données

- `n_per_class` = 150 profils par domaine
- `seed` = 42 (reproductible)
- Total de profils générés : 2250
- Profils avec étiquette bruitée (`label_noise=True`) : 145 (6.4%)
