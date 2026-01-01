#!/usr/bin/env python3
"""
Basic Llama-3.1-8B fine-tuning example using Tinker.

Run locally:
    python train_llama.py

Run in the cloud with vmux:
    vmux run python train_llama.py
    vmux run --detach python train_llama.py  # background

This fine-tunes Llama-3.1-8B on HuggingFace's NoRobots dataset
for instruction following.
"""

import asyncio

import chz
from tinker_cookbook import cli_utils, model_info
from tinker_cookbook.recipes.chat_sl import chat_datasets
from tinker_cookbook.renderers import TrainOnWhat
from tinker_cookbook.supervised import train
from tinker_cookbook.supervised.types import ChatDatasetBuilderCommonConfig


def build_config() -> train.Config:
    model_name = "meta-llama/Llama-3.1-8B"
    renderer_name = model_info.get_recommended_renderer_name(model_name)

    common_config = ChatDatasetBuilderCommonConfig(
        model_name_for_tokenizer=model_name,
        renderer_name=renderer_name,
        max_length=32768,
        batch_size=128,
        train_on_what=TrainOnWhat.ALL_ASSISTANT_MESSAGES,
    )

    dataset = chat_datasets.NoRobotsBuilder(common_config=common_config)

    blueprint = chz.Blueprint(train.Config).apply({
        "log_path": "/tmp/tinker-sl-basic",
        "model_name": model_name,
        "dataset_builder": dataset,
        "learning_rate": 2e-4,
        "lr_schedule": "linear",
        "num_epochs": 1,
        "eval_every": 8,
    })

    return blueprint.make()


def main():
    config = build_config()

    # Skip the interactive prompt - always delete existing logs in cloud
    cli_utils.check_log_dir(config.log_path, behavior_if_exists="delete")

    print("🚀 Starting Llama-3.1-8B fine-tuning...")
    print(f"   Model: {config.model_name}")
    print(f"   Log path: {config.log_path}")
    print(f"   Learning rate: {config.learning_rate}")
    print()

    asyncio.run(train.main(config))

    print()
    print("✅ Training complete!")


if __name__ == "__main__":
    main()
