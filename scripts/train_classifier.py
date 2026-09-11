import logging
import os

import joblib
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dummy simple sentences
SIMPLE_SENTENCES = [
    "What is the capital of France?",
    "How many days are in a week?",
    "Tell me a joke.",
    "What is 2 + 2?",
    "Who is the president of the United States?",
    "Translate 'hello' to Spanish.",
    "What time is it?",
    "How is the weather today?",
    "What color is the sky?",
    "Say hello world.",
    "Is it raining outside?",
    "What does a cat say?",
    "How old is the universe?",
    "What is the largest planet?",
    "Who wrote Hamlet?",
    "What is the speed of light?",
    "How do you spell banana?",
    "What is the square root of 16?",
    "What is my IP address?",
    "Who won the last Super Bowl?",
    "Name a type of dog.",
    "What is a prime number?",
    "How many continents are there?",
    "What is the longest river?",
    "What is the highest mountain?",
    "Where is the Eiffel Tower?",
    "What is the boiling point of water?",
    "What is photosynthesis?",
    "How does a compass work?",
    "What is a rainbow?",
    "Why is the sky blue?",
    "What is gravity?",
    "How many bones in the human body?",
    "What is DNA?",
    "What is an atom?",
    "What is a black hole?",
    "How do bees make honey?",
    "What is the smallest country?",
    "What is the capital of Japan?",
    "What is the biggest ocean?",
    "How many planets in our solar system?",
    "What is the fastest animal?",
    "How long is a marathon?",
    "What is a leap year?",
    "Who invented the telephone?",
    "What is the freezing point of water?",
    "What is a noun?",
    "What is a verb?",
    "What is an adjective?",
    "What is an adverb?",
]

# Dummy complex sentences
COMPLEX_SENTENCES = [
    "Explain the theory of relativity in detail, including its mathematical foundations.",
    "Write a Python script to scrape a website, handle pagination, and save data to a database.",
    "Compare and contrast the economic policies of the United States and China over the last decade.",
    "Summarize the plot of War and Peace, highlighting the main themes and character arcs.",
    "Design a scalable microservices architecture for an e-commerce platform.",
    "What are the philosophical implications of artificial general intelligence?",
    "Provide a comprehensive guide to setting up a Kubernetes cluster on AWS.",
    "Analyze the impact of climate change on global agriculture and food security.",
    "Explain the mechanics of quantum entanglement and its potential applications in computing.",
    "Write a detailed business plan for a tech startup in the renewable energy sector.",
    "Discuss the history and evolution of jazz music in the 20th century.",
    "How does the immune system differentiate between self and non-self cells?",
    "Write a short story about a time traveler who accidentally changes the course of history.",
    "Explain the intricacies of the Byzantine Generals Problem in distributed systems.",
    "Provide a step-by-step tutorial on building a full-stack web application with React and Node.js.",
    "Analyze the symbolism in F. Scott Fitzgerald's The Great Gatsby.",
    "What are the main differences between classical mechanics and quantum mechanics?",
    "Explain the process of cellular respiration and its importance to living organisms.",
    "Discuss the ethical considerations of gene editing technologies like CRISPR.",
    "How do black holes form and what happens to matter that falls into them?",
    "Write a research paper on the effects of social media on mental health.",
    "Explain the concept of neural networks and how they are trained using backpropagation.",
    "Provide a detailed analysis of the causes and consequences of the French Revolution.",
    "How does monetary policy affect inflation and unemployment?",
    "Write a comprehensive review of the latest advancements in natural language processing.",
    "Explain the principles of thermodynamics and how they apply to everyday life.",
    "Discuss the role of epigenetics in human development and disease.",
    "How does the global supply chain work and what are its vulnerabilities?",
    "Write a persuasive essay on the importance of space exploration.",
    "Explain the mathematics behind cryptography and secure communication protocols.",
    "Analyze the architectural significance of the Taj Mahal.",
    "What are the main theories regarding the origin of the universe?",
    "Explain the mechanisms of evolution by natural selection.",
    "Discuss the impact of the Industrial Revolution on society and the environment.",
    "How do vaccines work and why are they important for public health?",
    "Write a critical review of a recent popular movie or book.",
    "Explain the legal and political framework of the European Union.",
    "How does artificial intelligence impact the job market and the future of work?",
    "Discuss the cultural significance of the Renaissance period in Europe.",
    "Explain the biology of aging and the current research on extending human lifespan.",
    "How do financial markets function and what causes economic recessions?",
    "Write a detailed guide on how to invest in the stock market for beginners.",
    "Explain the psychology of human decision-making and cognitive biases.",
    "Discuss the importance of biodiversity and the threats it faces today.",
    "How does the internet work, from physical infrastructure to application protocols?",
    "Explain the concept of dark matter and dark energy in cosmology.",
    "Write a historical analysis of the Cold War and its global implications.",
    "How do different political systems approach the balance between individual liberty and state authority?",
    "Discuss the challenges and opportunities of urbanization in the 21st century.",
    "Explain the science behind climate modeling and predicting future environmental changes.",
]


def main() -> None:
    logger.info("Initializing SentenceTransformer...")
    transformer = SentenceTransformer("all-MiniLM-L6-v2")

    logger.info("Encoding simple sentences...")
    simple_embeddings = transformer.encode(SIMPLE_SENTENCES)

    logger.info("Encoding complex sentences...")
    complex_embeddings = transformer.encode(COMPLEX_SENTENCES)

    # 0 for simple, 1 for complex
    X = list(simple_embeddings) + list(complex_embeddings)
    y = [0] * len(SIMPLE_SENTENCES) + [1] * len(COMPLEX_SENTENCES)

    logger.info("Training LogisticRegression classifier...")
    clf = LogisticRegression(random_state=42)
    clf.fit(X, y)

    # Ensure models directory exists
    os.makedirs("models", exist_ok=True)

    model_path = "models/complexity_classifier.pkl"
    logger.info(f"Saving trained model to {model_path}...")
    joblib.dump(clf, model_path)

    logger.info("Done.")


if __name__ == "__main__":
    main()
