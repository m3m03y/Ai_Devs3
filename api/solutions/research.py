"""
Solution for task 17:
Prepare data for fine tuning and use it to classify samples
"""

import os
import json
import pandas as pd

from conf.logger import LOG
from common.file_processor import create_jsonl

RESOURCE_PATH = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S04E02")
CORRECT_FILENAME = "correct.txt"
INCORRECT_FILENAME = "incorrect.txt"
TRAIN_FILENAME = "train.jsonl"
VALIDATION_FILENAME = "val.jsonl"


def _load_and_prepare(
    file_path: str, label: str, train_ratio: float = 0.8
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(file_path, header=None)
    df["label"] = label
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    LOG.debug("Dataframe for file: %s loaded.", file_path)
    train_size = int(len(df) * train_ratio)
    train_df = df.iloc[:train_size]
    val_df = df.iloc[train_size:]
    LOG.debug("Dataframe split.")
    return train_df, val_df


def _create_dataset() -> tuple[list[dict], list[dict]]:
    correct_file = os.fspath(f"{RESOURCE_PATH}/{CORRECT_FILENAME}")
    incorrect_file = os.fspath(f"{RESOURCE_PATH}/{INCORRECT_FILENAME}")

    train_correct, val_correct = _load_and_prepare(correct_file, "correct")
    LOG.debug(
        "Correct dataset train: %d, validation: %d.",
        len(train_correct),
        len(val_correct),
    )
    train_incorrect, val_incorrect = _load_and_prepare(incorrect_file, "incorrect")
    LOG.debug(
        "Inorrect dataset train: %d, validation: %d.",
        len(train_incorrect),
        len(val_incorrect),
    )

    train_data = pd.concat([train_correct, train_incorrect], ignore_index=True)
    val_data = pd.concat([val_correct, val_incorrect], ignore_index=True)
    train_list = train_data.apply(
        lambda row: {"data": row[:-1].tolist(), "label": row["label"]}, axis=1
    ).tolist()
    val_list = val_data.apply(
        lambda row: {"data": row[:-1].tolist(), "label": row["label"]}, axis=1
    ).tolist()

    LOG.debug("Training data sample: %s.", train_list[:2])  # Display first 2 samples
    LOG.debug("Validation data sample: %s.", val_list[:2])
    return train_list, val_list


def _write_jsonl(dataset: list[dict], out_filename: str) -> None:
    out_file = os.fspath(f"{RESOURCE_PATH}/{out_filename}")
    if os.path.isfile(out_file):
        os.remove(out_file)
        LOG.debug("File %s deleted.", out_file)
    LOG.debug("Create jsonl file: %s.", out_file)
    with open(out_file, "w", encoding="UTF-8") as file:
        for line in dataset:
            file.write(json.dumps(line) + "\n")
    LOG.debug("Jsonl file saved successfully.")


def prepare_data() -> dict:
    """Loads files and prepare array of pairs: data and label"""
    LOG.info("Prepare data for fine-tunning...")
    train_dataset, val_dataset = _create_dataset()
    train_jsonl = create_jsonl(
        "Qualify research samples", train_dataset, "data", "label"
    )
    val_jsonl = create_jsonl("Qualify research samples", val_dataset, "data", "label")
    LOG.info("Jsonl datasets created.")
    _write_jsonl(train_jsonl, TRAIN_FILENAME)
    _write_jsonl(val_jsonl, VALIDATION_FILENAME)
    LOG.info("Jsonl files saved.")
    return {"status": "OK"}
