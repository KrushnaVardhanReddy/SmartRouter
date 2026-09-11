import logging
import os
from typing import Any

import joblib
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ClassifierEngine:
    def __init__(self, model_path: str = "models/complexity_classifier.pkl") -> None:
        self.model_path = model_path
        self.transformer: SentenceTransformer = SentenceTransformer("all-MiniLM-L6-v2")
        self.classifier: Any | None = None

        if os.path.exists(self.model_path):
            try:
                self.classifier = joblib.load(self.model_path)
                logger.info(f"Loaded classifier from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load classifier from {self.model_path}: {e}")
        else:
            logger.warning(
                f"Classifier model not found at {self.model_path}. "
                "Will use default score of 0.5."
            )

    def score_prompt(self, text: str) -> float:
        """
        Embeds the given text and returns a complexity score between 0.0 and 1.0.
        If the classifier is not loaded, returns 0.5.
        """
        if self.classifier is None:
            return 0.5

        embedding = self.transformer.encode([text])
        # predict_proba returns array of shape (n_samples, n_classes)
        # We assume class 1 is "complex"
        probabilities = self.classifier.predict_proba(embedding)
        return float(probabilities[0][1])
