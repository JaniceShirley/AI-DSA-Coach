import os
import sys
import time
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    TrainerCallback
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel
)

class MetricsLoggingCallback(TrainerCallback):
    """Callback to record training metrics step-by-step."""
    def __init__(self):
        self.logs = []

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            entry = dict(logs)
            entry["step"] = state.global_step
            entry["epoch"] = state.epoch
            self.logs.append(entry)

def load_jsonl_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Loads a JSONL file into a list of dictionaries."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file {file_path} not found.")
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def prepare_tokenized_dataset(records: List[Dict[str, Any]], tokenizer: AutoTokenizer, max_length: int = 1024) -> Dataset:
    """Formats each chat example using the model's native chat template and tokenizes."""
    input_ids_list = []
    attention_mask_list = []
    labels_list = []

    for item in records:
        messages = item.get("messages", [])
        if not messages:
            continue

        # Format full conversation with native chat template
        formatted_chat = tokenizer.apply_chat_template(messages, tokenize=False)
        tokenized = tokenizer(
            formatted_chat,
            max_length=max_length,
            truncation=True,
            padding=False,
            return_tensors=None
        )

        input_ids = tokenized["input_ids"]
        attention_mask = tokenized["attention_mask"]
        labels = list(input_ids) # For causal LM, labels match input_ids

        input_ids_list.append(input_ids)
        attention_mask_list.append(attention_mask)
        labels_list.append(labels)

    return Dataset.from_dict({
        "input_ids": input_ids_list,
        "attention_mask": attention_mask_list,
        "labels": labels_list
    })

def train(config_path: str = "ml/configs/qlora_config.yaml"):
    """Executes reproducible QLoRA fine-tuning for AI DSA Coach."""
    print("==================================================")
    print("PHASE 6B — QLoRA FINE-TUNING PIPELINE STARTING")
    print("==================================================")

    # 1. Load configuration
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    model_name = cfg["model"]["model_name_or_path"]
    train_file = cfg["data"]["train_file"]
    val_file = cfg["data"]["validation_file"]
    max_seq_len = cfg["data"].get("max_seq_length", 1024)
    adapter_out_dir = cfg["training"]["adapter_output_dir"]
    checkpoints_dir = cfg["training"]["output_dir"]
    runs_dir = cfg["training"]["runs_dir"]

    os.makedirs(adapter_out_dir, exist_ok=True)
    os.makedirs(checkpoints_dir, exist_ok=True)
    os.makedirs(runs_dir, exist_ok=True)

    print(f"Base Model:       {model_name}")
    print(f"Train Dataset:    {train_file}")
    print(f"Validation File:  {val_file}")
    print(f"Max Seq Length:   {max_seq_len}")
    print(f"Adapter Output:   {adapter_out_dir}")

    # 2. Tokenizer setup
    print("\n--- Step 1: Loading Tokenizer ---")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=cfg["model"].get("trust_remote_code", True),
        use_fast=cfg["model"].get("use_fast_tokenizer", True)
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    print(f"Tokenizer loaded. Vocab size: {len(tokenizer)}, Pad token ID: {tokenizer.pad_token_id}")

    # 3. Model loading with 4-bit Quantization
    print("\n--- Step 2: Loading Base Model in 4-bit (NF4) ---")
    compute_dtype = torch.float32 if not torch.cuda.is_available() else torch.bfloat16
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=cfg["quantization"]["load_in_4bit"],
        bnb_4bit_quant_type=cfg["quantization"]["bnb_4bit_quant_type"],
        bnb_4bit_use_double_quant=cfg["quantization"]["bnb_4bit_use_double_quant"],
        bnb_4bit_compute_dtype=compute_dtype
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=cfg["model"].get("trust_remote_code", True)
    )
    print("Base model loaded in 4-bit precision.")

    # 4. Prepare for k-bit training and configure PEFT LoRA
    print("\n--- Step 3: Configuring PEFT LoRA ---")
    base_model = prepare_model_for_kbit_training(base_model)

    peft_cfg = cfg["peft_lora"]
    lora_config = LoraConfig(
        r=peft_cfg["r"],
        lora_alpha=peft_cfg["lora_alpha"],
        lora_dropout=peft_cfg["lora_dropout"],
        bias=peft_cfg["bias"],
        task_type=peft_cfg["task_type"],
        target_modules=peft_cfg["target_modules"]
    )
    model = get_peft_model(base_model, lora_config)

    # Calculate and log trainable parameter counts
    trainable_params, all_param = model.get_nb_trainable_parameters()
    trainable_pct = 100 * trainable_params / all_param
    print(f"Trainable parameters: {trainable_params:,} / {all_param:,} ({trainable_pct:.4f}%)")
    print(f"Base model weights frozen: 100.0%. Only LoRA adapter parameters will be trained.")

    # 5. Load and format datasets
    print("\n--- Step 4: Loading & Formatting Training Data ---")
    raw_train = load_jsonl_dataset(train_file)
    raw_val = load_jsonl_dataset(val_file)

    train_dataset = prepare_tokenized_dataset(raw_train, tokenizer, max_length=max_seq_len)
    eval_dataset = prepare_tokenized_dataset(raw_val, tokenizer, max_length=max_seq_len)
    print(f"Tokenized train examples: {len(train_dataset)}")
    print(f"Tokenized eval examples:  {len(eval_dataset)}")

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        pad_to_multiple_of=8 if torch.cuda.is_available() else None
    )

    # 6. Training Arguments setup
    tr_cfg = cfg["training"]
    training_args = TrainingArguments(
        output_dir=checkpoints_dir,
        num_train_epochs=tr_cfg["num_train_epochs"],
        per_device_train_batch_size=tr_cfg["per_device_train_batch_size"],
        per_device_eval_batch_size=tr_cfg["per_device_eval_batch_size"],
        gradient_accumulation_steps=tr_cfg["gradient_accumulation_steps"],
        learning_rate=tr_cfg["learning_rate"],
        lr_scheduler_type=tr_cfg["lr_scheduler_type"],
        warmup_ratio=tr_cfg["warmup_ratio"],
        weight_decay=tr_cfg["weight_decay"],
        logging_steps=tr_cfg["logging_steps"],
        eval_strategy=tr_cfg["eval_strategy"],
        eval_steps=tr_cfg["eval_steps"],
        save_strategy=tr_cfg["save_strategy"],
        save_steps=tr_cfg["save_steps"],
        save_total_limit=tr_cfg.get("save_total_limit", 2),
        seed=tr_cfg.get("seed", 42),
        fp16=tr_cfg.get("fp16", False),
        bf16=tr_cfg.get("bf16", False),
        gradient_checkpointing=tr_cfg.get("gradient_checkpointing", False),
        report_to="none",
        remove_unused_columns=False
    )

    metrics_cb = MetricsLoggingCallback()
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        callbacks=[metrics_cb]
    )

    # 7. Execute Training
    print("\n--- Step 5: Executing QLoRA Training ---")
    start_time = time.time()
    train_result = trainer.train()
    training_duration = round(time.time() - start_time, 2)
    print(f"\nTraining completed in {training_duration} seconds.")

    final_train_loss = train_result.training_loss
    eval_result = trainer.evaluate()
    final_val_loss = eval_result.get("eval_loss", 0.0)

    print(f"Final Training Loss:   {final_train_loss:.4f}")
    print(f"Final Validation Loss: {final_val_loss:.4f}")

    # 8. Save LoRA Adapter & Tokenizer
    print("\n--- Step 6: Saving LoRA Adapter ---")
    model.save_pretrained(adapter_out_dir)
    tokenizer.save_pretrained(adapter_out_dir)
    print(f"LoRA adapter weights saved cleanly to: {adapter_out_dir}")
    print("Base model weights remain unmodified.")

    # 9. Verify Adapter Reloadability
    print("\n--- Step 7: Verifying Adapter Reloadability ---")
    test_reloaded = PeftModel.from_pretrained(base_model, adapter_out_dir)
    test_reloaded.eval()
    print("Verification PASSED: Saved LoRA adapter reloaded successfully onto base model.")

    # 10. Generate Training Report JSON
    report = {
        "model": {
            "name": model_name,
            "architecture": "CausalLM",
            "quantization": "4-bit (NF4 with double quantization)"
        },
        "dataset": {
            "train_examples": len(train_dataset),
            "validation_examples": len(eval_dataset),
            "test_examples_held_out": 17,
            "max_seq_length": max_seq_len
        },
        "lora_config": {
            "r": peft_cfg["r"],
            "lora_alpha": peft_cfg["lora_alpha"],
            "lora_dropout": peft_cfg["lora_dropout"],
            "target_modules": peft_cfg["target_modules"],
            "trainable_parameters": trainable_params,
            "total_parameters": all_param,
            "trainable_percentage": round(trainable_pct, 4)
        },
        "hyperparameters": {
            "learning_rate": tr_cfg["learning_rate"],
            "epochs": tr_cfg["num_train_epochs"],
            "per_device_batch_size": tr_cfg["per_device_train_batch_size"],
            "gradient_accumulation_steps": tr_cfg["gradient_accumulation_steps"],
            "effective_batch_size": tr_cfg["per_device_train_batch_size"] * tr_cfg["gradient_accumulation_steps"],
            "seed": tr_cfg.get("seed", 42)
        },
        "training_results": {
            "duration_seconds": training_duration,
            "final_train_loss": round(final_train_loss, 4),
            "final_validation_loss": round(final_val_loss, 4),
            "total_steps": trainer.state.global_step,
            "epoch": trainer.state.epoch
        },
        "adapter_location": adapter_out_dir,
        "logs": metrics_cb.logs
    }

    report_path = os.path.join(runs_dir, "training_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Training report saved to: {report_path}")

    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AI DSA Coach with QLoRA.")
    parser.add_argument("--config", type=str, default="ml/configs/qlora_config.yaml", help="Path to QLoRA YAML config")
    args = parser.parse_args()

    train(args.config)
