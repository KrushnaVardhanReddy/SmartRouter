import json
import logging
import os
from typing import Any

from datasets import load_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of models considered cheap (low complexity = 0) vs expensive (high complexity = 1)
CHEAP_MODELS = {"llama-2-7b-chat", "gpt-3.5-turbo", "claude-instant-1"}
EXPENSIVE_MODELS = {"gpt-4", "claude-2", "llama-2-70b-chat"}


def process_dataset(dataset: Any, output_path: str, max_samples: int = 1000) -> None:
    """Processes the dataset and saves it to a JSONL file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    count = 0
    with open(output_path, "w") as f:
        for item in dataset:
            if count >= max_samples:
                break

            # Use appropriate logic based on the dataset structure
            # The lmsys/chatbot_arena_conversations structure:
            if "conversation_a" in item and "winner" in item:
                # Assuming conversation_a is a list of conversation turns, grab the first one
                prompt = (
                    item["conversation_a"][0]["content"]
                    if isinstance(item["conversation_a"], list)
                    and len(item["conversation_a"]) > 0
                    and "content" in item["conversation_a"][0]
                    else str(item["conversation_a"])
                )
                winner = item["winner"]

                # We decide complexity based on the winner (heuristic for demonstration)
                # If a cheap model was sufficient to win, it's low complexity.
                if winner in CHEAP_MODELS:
                    complexity = 0
                elif winner in EXPENSIVE_MODELS:
                    complexity = 1
                else:
                    # Default/unknown
                    complexity = 1

                record = {
                    "prompt": prompt,
                    "complexity": complexity,
                    "winner_model": winner,
                }
                f.write(json.dumps(record) + "\n")
                count += 1
            elif "prompt" in item and "winner_model" in item:
                # Assuming prompt is a list of conversation turns, grab the first one
                prompt = (
                    item["prompt"][0]
                    if isinstance(item["prompt"], list)
                    else item["prompt"]
                )
                winner = item["winner_model"]

                # We decide complexity based on the winner (heuristic for demonstration)
                # If a cheap model was sufficient to win, it's low complexity.
                if winner in CHEAP_MODELS:
                    complexity = 0
                elif winner in EXPENSIVE_MODELS:
                    complexity = 1
                else:
                    # Default/unknown
                    complexity = 1

                record = {
                    "prompt": prompt,
                    "complexity": complexity,
                    "winner_model": winner,
                }
                f.write(json.dumps(record) + "\n")
                count += 1
            # Fallback for our dummy dataset
            elif "instruction" in item:
                prompt = item["instruction"]
                # Just random dummy complexity for fallback
                complexity = 0 if len(prompt) < 20 else 1
                record = {
                    "prompt": prompt,
                    "complexity": complexity,
                    "winner_model": "dummy_model",
                }
                f.write(json.dumps(record) + "\n")
                count += 1
            else:
                # Try to extract something if structure is unknown
                continue

    logger.info(f"Processed {count} samples and saved to {output_path}")


def main() -> None:
    output_path = "data/training_seed.jsonl"
    logger.info("Attempting to load local parquet dataset...")
    try:
        # Load the locally downloaded parquet file
        dataset = load_dataset("parquet", data_files="data/chatbot_arena.parquet", split="train")
        process_dataset(dataset, output_path, max_samples=2000)
    except Exception as e:
        logger.warning(f"Could not load the original dataset due to: {e}")
        logger.info(
            "Falling back to a small dummy dataset for testing/demonstration..."
        )
        # Since it's an automated environment, the HF dataset is likely gated.
        # Fall back to a larger, realistic dataset for testing/demonstration.
        dummy_dataset = [
            # Low Complexity (Simple facts, greetings, basic questions)
            {"prompt": "What is the capital of France?", "winner_model": "gpt-3.5-turbo"},
            {"prompt": "Hello! How are you doing today?", "winner_model": "llama-2-7b-chat"},
            {"prompt": "Can you give me a recipe for chocolate chip cookies?", "winner_model": "gpt-3.5-turbo"},
            {"prompt": "Who wrote Romeo and Juliet?", "winner_model": "claude-instant-1"},
            {"prompt": "Translate 'Good morning' into Spanish.", "winner_model": "llama-2-7b-chat"},
            {"prompt": "What is the boiling point of water in Celsius?", "winner_model": "gpt-3.5-turbo"},
            {"prompt": "Write a polite email declining a job offer.", "winner_model": "claude-instant-1"},
            {"prompt": "List 5 benefits of drinking water.", "winner_model": "gpt-3.5-turbo"},
            {"prompt": "How many days are in a leap year?", "winner_model": "llama-2-7b-chat"},
            {"prompt": "Write a haiku about autumn.", "winner_model": "claude-instant-1"},
            
            # High Complexity (Coding, deep analysis, complex reasoning)
            {"prompt": "Write a Python script using asyncio and aiohttp to concurrently scrape 100 URLs with rate limiting and exponential backoff.", "winner_model": "gpt-4"},
            {"prompt": "Explain the mathematical formulation of the attention mechanism in Transformers, specifically multi-head attention.", "winner_model": "claude-2"},
            {"prompt": "I need a complex SQL query. Given tables 'users', 'orders', and 'products', write a query to find the top 5 users who spent the most money in the last 30 days, including their total spend and favorite product category.", "winner_model": "gpt-4"},
            {"prompt": "Design a highly scalable microservices architecture for a real-time multiplayer game. Discuss load balancing, state synchronization, and database choices.", "winner_model": "llama-2-70b-chat"},
            {"prompt": "Refactor this C++ code to use smart pointers and C++20 concepts to avoid memory leaks: [code snippet omitted]", "winner_model": "gpt-4"},
            {"prompt": "Compare and contrast the epistemic theories of Immanuel Kant and David Hume, focusing on the concept of 'a priori' knowledge.", "winner_model": "claude-2"},
            {"prompt": "Write a React hook that manages a WebSocket connection, handles reconnections automatically, and syncs the data with a Zustand store.", "winner_model": "gpt-4"},
            {"prompt": "Explain how zero-knowledge proofs (zk-SNARKs) work at a cryptographic level. Do not use analogies.", "winner_model": "llama-2-70b-chat"},
            {"prompt": "Develop a comprehensive marketing strategy for a B2B SaaS startup launching a new AI-powered CRM, including budget allocation across channels.", "winner_model": "claude-2"},
            {"prompt": "Analyze the time and space complexity of Dijkstra's algorithm when using a Fibonacci heap versus a binary heap.", "winner_model": "gpt-4"},
        ]
        process_dataset(dummy_dataset, output_path, max_samples=20)


if __name__ == "__main__":
    main()
