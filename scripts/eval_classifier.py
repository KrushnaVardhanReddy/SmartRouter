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
    # Simple prompts (cheap) - 0. Everyday questions, greetings, short facts.
    {
        "prompt": "Hi, I'm trying to book a flight to London for next week. Can you tell me what the weather is usually like there in October? I just need a quick summary so I know what to pack.",
        "complexity": 0,
    },
    {
        "prompt": "Can you give me a really quick, 3-step recipe for making scrambled eggs? Just the basics, no fancy ingredients.",
        "complexity": 0,
    },
    {
        "prompt": "Translate this email into Spanish for me:\n\n'Dear team, we will be having our weekly sync at 10 AM tomorrow. Please make sure to bring your status updates. Thanks!'",
        "complexity": 0,
    },
    {
        "prompt": "What's the difference between a crocodile and an alligator? Just a short explanation is fine.",
        "complexity": 0,
    },
    {
        "prompt": "I'm writing a birthday card for my grandmother. She is turning 80. Could you suggest a short, sweet message I can write inside?",
        "complexity": 0,
    },
    {
        "prompt": "Write a 2-sentence summary of the movie The Matrix.",
        "complexity": 0,
    },
    {
        "prompt": "How many ounces are in a standard cup of liquid? I'm trying to follow a recipe and the conversions are confusing me.",
        "complexity": 0,
    },
    {
        "prompt": "Give me a quick bulleted list of 5 things I can do to improve my sleep hygiene tonight.",
        "complexity": 0,
    },
    {
        "prompt": "What is the capital of Australia? Is it Sydney or Melbourne? I always forget.",
        "complexity": 0,
    },
    {
        "prompt": "Write a short, polite email to my boss asking for next Friday off for a personal day.",
        "complexity": 0,
    },
    # Complex prompts (expensive) - 1. Coding, logic, deep analysis, large context.
    {
        "prompt": "I need to build a highly concurrent web scraper in Go. The scraper needs to read a list of 10,000 URLs from a PostgreSQL database, fetch the HTML, extract all the <a> tags using a robust DOM parser, and save the unique outbound links back to the database. It MUST handle rate limiting (max 50 req/sec), respect robots.txt, use a distributed pool of rotating proxies, and gracefully shut down on SIGINT. Please provide the complete architecture, database schema, and the core Go implementation using goroutines and channels.",
        "complexity": 1,
    },
    {
        "prompt": "Analyze the time and space complexity of the following algorithm. Then, refactor it to achieve O(N) time complexity using a monotonic deque. \n```python\ndef maxSlidingWindow(nums, k):\n    res = []\n    for i in range(len(nums) - k + 1):\n        res.append(max(nums[i:i+k]))\n    return res\n```\nExplain mathematically why the monotonic deque approaches O(N) amortized time.",
        "complexity": 1,
    },
    {
        "prompt": "Act as a senior DevOps engineer. I am currently running a monolithic Node.js application on a single EC2 instance. I want to migrate this to a highly available Kubernetes cluster on AWS (EKS). Outline a step-by-step migration plan covering: Dockerization strategies, Terraform infrastructure as code for the EKS cluster, setting up an Ingress controller with ALB, configuring Horizontal Pod Autoscaling (HPA) based on custom CPU metrics, and a zero-downtime CI/CD pipeline using GitHub Actions.",
        "complexity": 1,
    },
    {
        "prompt": "Critically compare and contrast the epistemic theories of Immanuel Kant and David Hume regarding the concept of 'a priori' knowledge. Specifically, how does Kant's 'synthetic a priori' resolve the empiricist skepticism introduced by Hume's fork? Use specific references to the 'Critique of Pure Reason' and 'An Enquiry Concerning Human Understanding'.",
        "complexity": 1,
    },
    {
        "prompt": "I am designing a real-time multiplayer chess backend. Players need to be matched based on an Elo rating system. Once matched, game state must be synchronized via WebSockets with latency under 50ms. How would you architect this using Redis Pub/Sub, Node.js WebSocket servers, and a persistent PostgreSQL store? Specifically address how you would handle network partitions, client reconnects mid-game, and ensuring that moves are processed exactly-once.",
        "complexity": 1,
    },
    {
        "prompt": "Write a comprehensive review of the current state of Quantum Error Correction (QEC). Focus on the Surface Code architecture. Explain the threshold theorem, the physical vs logical qubit overhead, and how decoding algorithms like Minimum Weight Perfect Matching (MWPM) scale with the distance of the code. Conclude with a realistic timeline for fault-tolerant quantum computing based on recent experimental papers.",
        "complexity": 1,
    },
    {
        "prompt": "You are a seasoned M&A financial analyst. Create a detailed financial modeling framework for a leveraged buyout (LBO) of a mid-market SaaS company. Walk me through how you project free cash flows, calculate the Weighted Average Cost of Capital (WACC), structure the debt tranches (Senior, Mezzanine, PIK), and ultimately calculate the Internal Rate of Return (IRR) for the private equity sponsor over a 5-year hold period. What are the key sensitivity drivers?",
        "complexity": 1,
    },
    {
        "prompt": "Write a complete, secure Smart Contract in Solidity (v0.8.20+) for a decentralized escrow service. Two parties deposit ERC20 tokens. A designated third-party arbitrator holds the key to release the funds to either party or split them. The contract must protect against reentrancy attacks, use OpenZeppelin's SafeERC20, and emit indexed events for all state changes. Provide the code and a breakdown of the security considerations.",
        "complexity": 1,
    },
    {
        "prompt": "Explain the biochemical and thermodynamic pathways of the Krebs cycle (Citric Acid Cycle) in extreme detail. Map out every single enzyme, intermediate molecule, and coenzyme involved. Calculate the exact ATP yield per molecule of glucose, taking into account the P/O ratios for NADH and FADH2 in the electron transport chain, and explain how the cycle is allosterically regulated during periods of high cellular ATP/ADP ratios.",
        "complexity": 1,
    },
    {
        "prompt": "Write a React application using Next.js 14 (App Router) that implements a complex multi-step form with dynamic validation. The form needs to collect user data, employment history (which is an array of objects where users can add/remove jobs), and upload a PDF resume. Use React Hook Form with Zod for strict schema validation. The UI must be fully accessible (a11y compliant) and use Tailwind CSS for styling. Show me the complete component tree and the Zod schema.",
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
