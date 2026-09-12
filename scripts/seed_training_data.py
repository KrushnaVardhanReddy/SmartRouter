import json
import logging
import os

from datasets import load_dataset  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting seed data extraction...")

    try:
        # Load the dataset
        logger.info("Loading lmsys/chatbot_arena_conversations dataset...")
        dataset = load_dataset("lmsys/chatbot_arena_conversations", split="train")

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        output_file = "data/training_seed.jsonl"
        logger.info(f"Writing to {output_file}...")

        count = 0
        with open(output_file, "w") as f:
            for item in dataset:  # type: ignore
                # In the lmsys dataset, 'winner_model_a', 'winner_model_b', 'winner_tie' are usually keys
                # We simplify by just extracting the first user prompt and deciding complexity based on model

                # Try to find the prompt
                prompt = ""
                if "question_id" in item and "conversation_a" in item:
                    # typical schema
                    conv = item["conversation_a"]
                    if conv and len(conv) > 0 and conv[0].get("role") == "user":
                        prompt = conv[0].get("content", "")

                if not prompt:
                    continue

                winner = (
                    item.get("winner_model_a", 0) == 1
                    and item.get("model_a", "")
                    or item.get("winner_model_b", 0) == 1
                    and item.get("model_b", "")
                    or ""
                )

                if not winner:
                    continue

                # Simplistic complexity mapping:
                # If a cheap/fast model won, it might be low complexity.
                # If only an expensive model won, high complexity.
                # Here we just use some dummy logic to generate seed labels for training
                cheap_models = ["llama-2-7b", "mistral-7b", "gemma-7b"]
                is_complex = 1
                for cheap in cheap_models:
                    if cheap in winner.lower():
                        is_complex = 0
                        break

                record = {
                    "prompt": prompt,
                    "winner_model": winner,
                    "is_complex": is_complex,
                }

                f.write(json.dumps(record) + "\n")
                count += 1

                if count >= 1000:  # Just extract a subset for seeding
                    break

        logger.info(f"Successfully extracted {count} records to {output_file}.")

    except Exception as e:
        logger.warning(f"Failed to load HuggingFace dataset: {e}")
        logger.info(
            "Creating a local fallback dataset since HuggingFace access failed..."
        )

        os.makedirs("data", exist_ok=True)
        output_file = "data/training_seed.jsonl"

        fallback_data = [
            {
                "prompt": "What is the capital of France?",
                "winner_model": "mistral-7b",
                "is_complex": 0,
            },
            {
                "prompt": "Write a complex Python script for scraping and parallel processing.",
                "winner_model": "gpt-4",
                "is_complex": 1,
            },
            {"prompt": "Say hello.", "winner_model": "llama-2-7b", "is_complex": 0},
            {
                "prompt": "Explain quantum entanglement in detail with math.",
                "winner_model": "claude-3-opus",
                "is_complex": 1,
            },
        ]

        with open(output_file, "w") as f:
            for item in fallback_data:
                f.write(json.dumps(item) + "\n")

        logger.info(f"Wrote {len(fallback_data)} fallback records to {output_file}.")


if __name__ == "__main__":
    main()
