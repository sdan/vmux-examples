#!/usr/bin/env python3
"""
Teach a LLM to add numbers using reinforcement learning.

This is the "hello world" of RL fine-tuning - simple enough to run fast,
but you can actually watch the model learn in real-time!

Run locally:
    TINKER_API_KEY=xxx python train_arithmetic.py

Run in the cloud with vmux:
    vmux run python train_arithmetic.py

Expected behavior:
    - Reward starts around 0.66 (model guesses randomly)
    - Reward climbs to 1.0 within the first few training steps
    - The model learns: "What is X + Y?" -> "X+Y"
"""

import asyncio

import chz
from tinker_cookbook import cli_utils, model_info
from tinker_cookbook.recipes.math_rl.arithmetic_env import ArithmeticDatasetBuilder
from tinker_cookbook.rl import train


def build_config() -> train.Config:
    # Use smaller model for faster iteration
    model_name = "meta-llama/Llama-3.2-1B"
    renderer_name = model_info.get_recommended_renderer_name(model_name)

    # Arithmetic dataset: "What is X + Y?" problems
    dataset = ArithmeticDatasetBuilder(
        batch_size=100,          # 100 problems per batch
        group_size=4,            # 4 attempts per problem (for variance reduction)
        model_name_for_tokenizer=model_name,
        renderer_name=renderer_name,
        n_batches=100,           # Total training batches
        include_fewshot=True,    # Include "What is 4+5? -> 9" example
    )

    blueprint = chz.Blueprint(train.Config).apply({
        "log_path": "/tmp/tinker-arithmetic",
        "model_name": model_name,
        "dataset_builder": dataset,
        "learning_rate": 1e-4,   # Aggressive LR since task is simple
        "max_tokens": 5,         # Answer is just a number
        "eval_every": 0,         # Skip evals for speed
    })

    return blueprint.make()


def main():
    config = build_config()

    # Delete existing logs and start fresh
    cli_utils.check_log_dir(config.log_path, behavior_if_exists="delete")

    print("🧮 Teaching a LLM to add numbers...")
    print(f"   Model: {config.model_name}")
    print(f"   Task: 'What is X + Y?' -> answer")
    print(f"   Log path: {config.log_path}")
    print()
    print("   Watch for reward to go from ~0.66 → 1.0")
    print()

    asyncio.run(train.main(config))

    print()
    print("✅ Model learned arithmetic!")


if __name__ == "__main__":
    main()
