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
    logger.info("Attempting to load 'lmsys/chatbot_arena_conversations'...")
    try:
        dataset = load_dataset(
            "lmsys/chatbot_arena_conversations", split="train", streaming=True
        )
        process_dataset(dataset, output_path)
    except Exception as e:
        logger.warning(f"Could not load the original dataset due to: {e}")
        logger.info(
            "Falling back to a small dummy dataset for testing/demonstration..."
        )
        # Since it's an automated environment, the HF dataset is likely gated.
        # Fall back to a dummy list of dicts.
        dummy_dataset = [
            {"prompt": "Hello world", "winner_model": "gpt-3.5-turbo"},
            {"prompt": "Explain quantum entanglement", "winner_model": "gpt-4"},
            {"prompt": "Write a python script", "winner_model": "gpt-4"},
            {"prompt": "What is 2+2", "winner_model": "llama-2-7b-chat"},
        ]
        process_dataset(dummy_dataset, output_path, max_samples=4)


if __name__ == "__main__":
    main()
