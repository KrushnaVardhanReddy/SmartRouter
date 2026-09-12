import asyncio
import json
import logging
import os
from typing import Any

import openai
from datasets import load_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI router. Your job is to classify the computational complexity and reasoning depth required to answer a given user prompt.
Score the complexity as strictly 0 or 1.

Rubric:
0 (Simple): The prompt requires minimal reasoning, basic facts, simple greetings, or straightforward tasks.
1 (Complex): The prompt requires deep reasoning, strict constraint adherence (like JSON schema enforcement), complex coding, or specialized domain knowledge.

Output exactly a JSON object in this format: {"complexity": <0 or 1>}
"""


async def evaluate_complexity_with_llm(prompt: str, client: openai.AsyncOpenAI | None = None) -> int:
    """Uses LLM-as-a-judge to evaluate prompt complexity (0 or 1)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not client:
        logger.debug("OPENAI_API_KEY not found or client not provided. Using dummy fallback complexity.")
        return 0 if len(prompt) < 20 else 1

    retry_count = 0
    max_retries = 5
    base_delay = 1.0

    while retry_count <= max_retries:
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=10,
            )
            content = response.choices[0].message.content
            if not content:
                return 1
            result = json.loads(content)
            return int(result.get("complexity", 1))
        except openai.RateLimitError as e:
            if retry_count == max_retries:
                logger.warning(f"Rate limit exceeded after {max_retries} retries: {e}. Falling back to dummy logic.")
                return 0 if len(prompt) < 20 else 1
            delay = base_delay * (2 ** retry_count)
            logger.info(f"Rate limit hit. Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
            retry_count += 1
        except Exception as e:
            logger.warning(f"LLM-as-a-judge failed: {e}. Falling back to dummy logic.")
            return 0 if len(prompt) < 20 else 1

    return 0 if len(prompt) < 20 else 1


async def process_dataset(dataset: Any, output_path: str, max_samples: int = 10000) -> None:
    """Processes the dataset and saves it to a JSONL file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.AsyncOpenAI(api_key=api_key) if api_key else None

    semaphore = asyncio.Semaphore(20)

    async def process_item(item: dict[str, Any]) -> dict[str, Any] | None:
        async with semaphore:
            if "conversation_a" in item and "winner" in item:
                prompt = (
                    item["conversation_a"][0]["content"]
                    if isinstance(item["conversation_a"], list)
                    and len(item["conversation_a"]) > 0
                    and "content" in item["conversation_a"][0]
                    else str(item["conversation_a"])
                )
                winner = item["winner"]
            elif "prompt" in item and "winner_model" in item:
                prompt = (
                    item["prompt"][0]
                    if isinstance(item["prompt"], list)
                    else item["prompt"]
                )
                winner = item["winner_model"]
            elif "instruction" in item:
                prompt = item["instruction"]
                winner = "dummy_model"
            else:
                return None

            complexity = await evaluate_complexity_with_llm(prompt, client)
            return {
                "prompt": prompt,
                "complexity": complexity,
                "winner_model": winner,
            }

    tasks = []
    count = 0
    for item in dataset:
        if count >= max_samples:
            break

        # Quick validation before task creation to correctly count
        if ("conversation_a" in item and "winner" in item) or \
           ("prompt" in item and "winner_model" in item) or \
           ("instruction" in item):
            tasks.append(process_item(item))
            count += 1

    results = await asyncio.gather(*tasks)

    with open(output_path, "w") as f:  # noqa: ASYNC230
        for result in results:
            if result is not None:
                f.write(json.dumps(result) + "\n")

    logger.info(f"Processed {count} samples and saved to {output_path}")


async def main_async() -> None:
    output_path = "data/training_seed.jsonl"
    logger.info("Attempting to load local parquet dataset...")
    try:
        # Load the locally downloaded parquet file
        dataset = load_dataset(
            "parquet", data_files="data/chatbot_arena.parquet", split="train"
        )
        await process_dataset(dataset, output_path, max_samples=10000)
    except Exception as e:
        logger.warning(f"Could not load the original dataset due to: {e}")
        logger.info(
            "Falling back to a small dummy dataset for testing/demonstration..."
        )
        # Since it's an automated environment, the HF dataset is likely gated.
        # Fall back to a larger, realistic dataset for testing/demonstration.
        dummy_dataset = [
            # Low Complexity (Simple facts, greetings, basic questions)
            {
                "prompt": "What is the capital of France?",
                "winner_model": "gpt-3.5-turbo",
            },
            {
                "prompt": "Hello! How are you doing today?",
                "winner_model": "llama-2-7b-chat",
            },
            {
                "prompt": "Can you give me a recipe for chocolate chip cookies?",
                "winner_model": "gpt-3.5-turbo",
            },
            {
                "prompt": "Who wrote Romeo and Juliet?",
                "winner_model": "claude-instant-1",
            },
            {
                "prompt": "Translate 'Good morning' into Spanish.",
                "winner_model": "llama-2-7b-chat",
            },
            {
                "prompt": "What is the boiling point of water in Celsius?",
                "winner_model": "gpt-3.5-turbo",
            },
            {
                "prompt": "Write a polite email declining a job offer.",
                "winner_model": "claude-instant-1",
            },
            {
                "prompt": "List 5 benefits of drinking water.",
                "winner_model": "gpt-3.5-turbo",
            },
            {
                "prompt": "How many days are in a leap year?",
                "winner_model": "llama-2-7b-chat",
            },
            {
                "prompt": "Write a haiku about autumn.",
                "winner_model": "claude-instant-1",
            },
            # High Complexity (Coding, deep analysis, complex reasoning)
            {
                "prompt": "Write a Python script using asyncio and aiohttp to concurrently scrape 100 URLs with rate limiting and exponential backoff.",
                "winner_model": "gpt-4",
            },
            {
                "prompt": "Explain the mathematical formulation of the attention mechanism in Transformers, specifically multi-head attention.",
                "winner_model": "claude-2",
            },
            {
                "prompt": "I need a complex SQL query. Given tables 'users', 'orders', and 'products', write a query to find the top 5 users who spent the most money in the last 30 days, including their total spend and favorite product category.",
                "winner_model": "gpt-4",
            },
            {
                "prompt": "Design a highly scalable microservices architecture for a real-time multiplayer game. Discuss load balancing, state synchronization, and database choices.",
                "winner_model": "llama-2-70b-chat",
            },
            {
                "prompt": "Refactor this C++ code to use smart pointers and C++20 concepts to avoid memory leaks: [code snippet omitted]",
                "winner_model": "gpt-4",
            },
            {
                "prompt": "Compare and contrast the epistemic theories of Immanuel Kant and David Hume, focusing on the concept of 'a priori' knowledge.",
                "winner_model": "claude-2",
            },
            {
                "prompt": "Write a React hook that manages a WebSocket connection, handles reconnections automatically, and syncs the data with a Zustand store.",
                "winner_model": "gpt-4",
            },
            {
                "prompt": "Explain how zero-knowledge proofs (zk-SNARKs) work at a cryptographic level. Do not use analogies.",
                "winner_model": "llama-2-70b-chat",
            },
            {
                "prompt": "Develop a comprehensive marketing strategy for a B2B SaaS startup launching a new AI-powered CRM, including budget allocation across channels.",
                "winner_model": "claude-2",
            },
            {
                "prompt": "Analyze the time and space complexity of Dijkstra's algorithm when using a Fibonacci heap versus a binary heap.",
                "winner_model": "gpt-4",
            },
        ]
        await process_dataset(dummy_dataset, output_path, max_samples=20)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
