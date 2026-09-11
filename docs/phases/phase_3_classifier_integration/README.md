# Phase 3: Classifier Integration

1. Adapt the `train_classifier.py` script from the `Local_AI_Assistant` project to generate a `complexity_classifier.pkl`.
2. Implement the `classifier/engine.py` to load the embeddings model and the `.pkl` file.
3. Hook the classifier into the request lifecycle to generate a `0.0 - 1.0` score before routing.
