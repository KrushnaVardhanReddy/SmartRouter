import logging
import os
import sys

import joblib  # type: ignore
from sentence_transformers import SentenceTransformer  # type: ignore
from sklearn.metrics import classification_report  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOLDEN_PROMPTS = [
    {"prompt": "Hi", "is_complex": 0},
    {"prompt": "What is 2+2?", "is_complex": 0},
    {"prompt": "Translate this to French: apple", "is_complex": 0},
    {"prompt": "Tell me a joke", "is_complex": 0},
    {"prompt": "What is the capital of Spain?", "is_complex": 0},
    {
        "prompt": "Write a 500-word essay analyzing the socio-economic impacts of the Industrial Revolution on Victorian London, citing at least three primary sources.",
        "is_complex": 1,
    },
    {
        "prompt": "Explain the architectural differences between Transformer models and LSTMs, detailing how self-attention mechanisms solve the vanishing gradient problem.",
        "is_complex": 1,
    },
    {
        "prompt": "Provide a complete React front-end application with state management using Redux, including routing and a mocked API integration layer.",
        "is_complex": 1,
    },
    {"prompt": "What color is the sky?", "is_complex": 0},
    {"prompt": "Hello world", "is_complex": 0},
    {"prompt": "How many states in the US?", "is_complex": 0},
    {
        "prompt": "Design a highly available and scalable distributed database system architecture for a global e-commerce platform handling millions of transactions per second.",
        "is_complex": 1,
    },
    {"prompt": "Is water wet?", "is_complex": 0},
    {"prompt": "Who is the CEO of Tesla?", "is_complex": 0},
    {
        "prompt": "Analyze the time and space complexity of Dijkstra's algorithm implemented with a Fibonacci heap compared to a binary heap.",
        "is_complex": 1,
    },
    {"prompt": "When is Christmas?", "is_complex": 0},
    {"prompt": "Write a short poem about a cat.", "is_complex": 0},
    {"prompt": "Summarize the plot of the Matrix.", "is_complex": 1},
    {
        "prompt": "Create a detailed 3-month workout plan for a beginner focusing on hypertrophy, including diet recommendations.",
        "is_complex": 1,
    },
    {"prompt": "What is the largest planet?", "is_complex": 0},
    {"prompt": "Who wrote Hamlet?", "is_complex": 0},
    {
        "prompt": "Write a comprehensive literature review on the applications of CRISPR-Cas9 in agricultural biotechnology.",
        "is_complex": 1,
    },
    {
        "prompt": "Implement a full CI/CD pipeline script for a monorepo using GitHub Actions, including testing, linting, and Docker deployments to AWS ECS.",
        "is_complex": 1,
    },
    {"prompt": "What sound does a cow make?", "is_complex": 0},
    {"prompt": "Convert 10 km to miles.", "is_complex": 0},
    {"prompt": "Explain quantum entanglement.", "is_complex": 1},
    {"prompt": "How do I boil an egg?", "is_complex": 0},
    {
        "prompt": "Write a detailed financial projection for a SaaS startup over 5 years, including CAC, LTV, and churn rate calculations.",
        "is_complex": 1,
    },
    {"prompt": "What is the speed of light?", "is_complex": 0},
    {"prompt": "Who is the president?", "is_complex": 0},
    {
        "prompt": "Develop a multi-agent reinforcement learning simulation in Python to optimize traffic light control in a grid network.",
        "is_complex": 1,
    },
    {"prompt": "Is the earth flat?", "is_complex": 0},
    {"prompt": "Translate 'thank you' to German.", "is_complex": 0},
    {
        "prompt": "Explain the philosophical implications of Nietzsche's 'God is dead' statement in the context of modern secularism.",
        "is_complex": 1,
    },
    {
        "prompt": "Write a Bash script to monitor server health, check disk space, and send an email alert if CPU usage exceeds 90% for 5 minutes.",
        "is_complex": 1,
    },
    {"prompt": "What is 10*10?", "is_complex": 0},
    {"prompt": "Name a fruit.", "is_complex": 0},
    {
        "prompt": "Compare and contrast the economic policies of Keynes and Hayek regarding government intervention during a recession.",
        "is_complex": 1,
    },
    {"prompt": "What is photosynthesis?", "is_complex": 0},
    {
        "prompt": "Write a Python script to scrape a dynamically loaded React webpage using Selenium and parse the data into a Pandas DataFrame.",
        "is_complex": 1,
    },
    {"prompt": "How many days in a leap year?", "is_complex": 0},
    {"prompt": "What is the boiling point of water?", "is_complex": 0},
    {
        "prompt": "Design a complete RESTful API spec using OpenAPI 3.0 for a library management system.",
        "is_complex": 1,
    },
    {"prompt": "Who won the last Super Bowl?", "is_complex": 0},
    {
        "prompt": "Explain the mechanisms of horizontal gene transfer in bacteria and its implications for antibiotic resistance.",
        "is_complex": 1,
    },
    {"prompt": "How old is the universe?", "is_complex": 0},
    {
        "prompt": "Write a C++ program implementing a custom memory allocator tailored for a high-frequency trading application.",
        "is_complex": 1,
    },
    {"prompt": "What is a noun?", "is_complex": 0},
    {"prompt": "Write a haiku about winter.", "is_complex": 0},
    {
        "prompt": "Explain the theory of general relativity and how it differs from special relativity.",
        "is_complex": 1,
    },
]


def main() -> None:
    logger.info("Starting classifier evaluation...")

    model_path = "models/complexity_classifier.pkl"
    if not os.path.exists(model_path):
        logger.error(
            f"Model file not found at {model_path}. Please train the model first."
        )
        sys.exit(1)

    logger.info(f"Loading classifier from {model_path}...")
    clf = joblib.load(model_path)

    logger.info("Initializing SentenceTransformer...")
    transformer = SentenceTransformer("all-MiniLM-L6-v2")

    prompts = [item["prompt"] for item in GOLDEN_PROMPTS]
    true_labels = [item["is_complex"] for item in GOLDEN_PROMPTS]

    logger.info("Encoding golden prompts...")
    embeddings = transformer.encode(prompts)

    logger.info("Running inference...")
    predicted_labels = clf.predict(embeddings)

    logger.info("Evaluation Results:")
    report = classification_report(
        true_labels, predicted_labels, target_names=["Simple (0)", "Complex (1)"]
    )
    print(report)


if __name__ == "__main__":
    main()
