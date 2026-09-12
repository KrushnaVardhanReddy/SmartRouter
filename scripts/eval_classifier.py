import logging
import os

import joblib
from sentence_transformers import SentenceTransformer
from sklearn.metrics import classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A small golden dataset with known complexity
# 0 for simple (cheap), 1 for complex (expensive)
GOLDEN_DATASET = [
    # Simple prompts (cheap) - 0
    {"prompt": "What time is it in Tokyo?", "complexity": 0},
    {"prompt": "Say hello to my little friend.", "complexity": 0},
    {"prompt": "How many days in May?", "complexity": 0},
    {"prompt": "What is the capital of Spain?", "complexity": 0},
    {"prompt": "Who is the CEO of Apple?", "complexity": 0},
    {"prompt": "Can you bark like a dog?", "complexity": 0},
    {"prompt": "Translate 'good morning' to French.", "complexity": 0},
    {"prompt": "What is 10 + 15?", "complexity": 0},
    {"prompt": "Are tomatoes fruits or vegetables?", "complexity": 0},
    {"prompt": "Where is the Eiffel tower located?", "complexity": 0},
    {"prompt": "How many legs does a spider have?", "complexity": 0},
    {"prompt": "What is the largest ocean on Earth?", "complexity": 0},
    {"prompt": "Who wrote 'Romeo and Juliet'?", "complexity": 0},
    {"prompt": "What color is a ripe banana?", "complexity": 0},
    {"prompt": "How many states are in the US?", "complexity": 0},
    {"prompt": "What is the opposite of hot?", "complexity": 0},
    {"prompt": "Spell the word 'accommodate'.", "complexity": 0},
    {"prompt": "When is Valentine's Day?", "complexity": 0},
    {"prompt": "What is a baby cat called?", "complexity": 0},
    {"prompt": "What is the primary language spoken in Brazil?", "complexity": 0},
    {"prompt": "How many players are on a soccer team?", "complexity": 0},
    {"prompt": "What is the boiling point of water in Celsius?", "complexity": 0},
    {"prompt": "Who painted the Mona Lisa?", "complexity": 0},
    {"prompt": "What is the largest mammal?", "complexity": 0},
    {"prompt": "What is the symbol for Iron on the periodic table?", "complexity": 0},
    # Complex prompts (expensive) - 1
    {
        "prompt": "Implement a fully working neural network in C from scratch.",
        "complexity": 1,
    },
    {
        "prompt": "Analyze the socioeconomic impact of the 2008 financial crisis on millennials.",
        "complexity": 1,
    },
    {
        "prompt": "Write a multi-threaded web scraper in Rust that bypasses cloudflare.",
        "complexity": 1,
    },
    {
        "prompt": "Explain the mathematical proof of Fermat's Last Theorem.",
        "complexity": 1,
    },
    {
        "prompt": "Compare and contrast the philosophical theories of Kant and Nietzsche.",
        "complexity": 1,
    },
    {
        "prompt": "Design a distributed database architecture for a high-frequency trading platform.",
        "complexity": 1,
    },
    {
        "prompt": "Write a comprehensive review of the latest advancements in quantum error correction.",
        "complexity": 1,
    },
    {
        "prompt": "Explain the biochemical pathways of the Krebs cycle in detail.",
        "complexity": 1,
    },
    {
        "prompt": "Develop a business strategy for a new EV startup entering the European market.",
        "complexity": 1,
    },
    {
        "prompt": "Analyze the recurring motifs in the cinematic works of Andrei Tarkovsky.",
        "complexity": 1,
    },
    {
        "prompt": "Write a Python script to perform sentiment analysis on Twitter data using BERT.",
        "complexity": 1,
    },
    {
        "prompt": "Explain the concept of gauge symmetry in particle physics.",
        "complexity": 1,
    },
    {
        "prompt": "Discuss the implications of CRISPR-Cas9 on future human evolution.",
        "complexity": 1,
    },
    {
        "prompt": "Design a scalable API rate limiting system using Redis.",
        "complexity": 1,
    },
    {
        "prompt": "Write an essay on the role of artificial intelligence in modern warfare.",
        "complexity": 1,
    },
    {
        "prompt": "Explain the principles of topological quantum computing.",
        "complexity": 1,
    },
    {
        "prompt": "Analyze the geopolitical consequences of melting Arctic ice.",
        "complexity": 1,
    },
    {
        "prompt": "Write a smart contract in Solidity for a decentralized autonomous organization.",
        "complexity": 1,
    },
    {
        "prompt": "Discuss the ethical challenges of deploying autonomous vehicles in urban environments.",
        "complexity": 1,
    },
    {
        "prompt": "Explain the mechanics of the CRISPR-Cas9 gene editing tool.",
        "complexity": 1,
    },
    {
        "prompt": "Design a fault-tolerant microservices architecture for an e-commerce platform.",
        "complexity": 1,
    },
    {
        "prompt": "Write a research proposal on the effects of microplastics on marine ecosystems.",
        "complexity": 1,
    },
    {
        "prompt": "Analyze the impact of social media algorithms on political polarization.",
        "complexity": 1,
    },
    {
        "prompt": "Explain the theory of general relativity and its observational evidence.",
        "complexity": 1,
    },
    {
        "prompt": "Develop a comprehensive marketing plan for a new plant-based meat alternative.",
        "complexity": 1,
    },
]


def main() -> None:
    model_path = "models/complexity_classifier.pkl"
    if not os.path.exists(model_path):
        logger.error(f"Model file {model_path} not found. Please train it first.")
        return

    logger.info(f"Loading classifier from {model_path}...")
    try:
        clf = joblib.load(model_path)
    except Exception as e:
        logger.error(f"Failed to load the classifier: {e}")
        return

    logger.info("Initializing SentenceTransformer...")
    transformer = SentenceTransformer("all-MiniLM-L6-v2")

    prompts = [item["prompt"] for item in GOLDEN_DATASET]
    y_true = [item["complexity"] for item in GOLDEN_DATASET]

    logger.info("Encoding golden prompts...")
    embeddings = transformer.encode(prompts)

    logger.info("Making predictions...")
    y_pred = clf.predict(list(embeddings))

    logger.info("\nClassification Report:\n")
    report = classification_report(
        y_true, y_pred, target_names=["Simple (0)", "Complex (1)"]
    )
    print(report)


if __name__ == "__main__":
    main()
