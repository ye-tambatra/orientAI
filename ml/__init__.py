"""Machine Learning components of ORIENT'IA (Phase 2 of the project brief).

Sub-modules:
- xlsx_reader: dependency-free .xlsx reader (stdlib only)
- filieres:    grounded metadata about the 16 ISPM filières (used as the
               model's label space and as the synthetic-data generator's
               ground truth)
- vocab:       canonical vocabularies (matières, compétences, intérêts) and
               free-text -> canonical tag normalisation
- synthetic:   documented synthetic profile generator (training data)
- survey:      loader for the real survey responses (validation/test data)
               + traceability register writer
- features:    profile -> numeric feature vector encoder
- models:      from-scratch (numpy only) classifiers: majority/nearest-
               centroid baseline, k-NN, multinomial logistic regression
- metrics:     evaluation metrics (accuracy, top-k, macro-F1, confusion
               matrix, MRR, calibration, stability)
- train:       orchestrates loading, training, evaluation and writes the
               artifacts under ml/artifacts/
- inference:   OrientationModel, the object the conversational tools call
"""
