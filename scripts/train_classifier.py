import json
import logging
import os

import joblib
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    logger.info("Initializing SentenceTransformer...")
    transformer = SentenceTransformer("all-MiniLM-L6-v2")

    prompts = []
    labels = []

    data_file = "data/training_seed.jsonl"
    logger.info(f"Loading data from {data_file}...")
    try:
        with open(data_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                prompts.append(record["prompt"])
                labels.append(record["complexity"])
    except Exception as e:
        logger.error(f"Failed to load {data_file}: {e}")
        return

    logger.info(f"Encoding {len(prompts)} sentences...")
    X = transformer.encode(prompts)
    y = labels

    logger.info("Training LogisticRegression classifier...")
    clf = LogisticRegression(random_state=42, max_iter=1000)
    clf.fit(X, y)

    os.makedirs("models", exist_ok=True)
    model_path = "models/complexity_classifier.pkl"
    logger.info(f"Saving trained model to {model_path}...")
    joblib.dump(clf, model_path)

    logger.info("Done.")

if __name__ == "__main__":
    main()
