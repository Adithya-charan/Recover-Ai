import os
import json
from pathlib import Path
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType

try:
    from trl import SFTTrainer
    TRL_AVAILABLE = False  # Force fallback to standard Trainer for compatibility
except ImportError:
    TRL_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "llm" / "train.jsonl"
OUTPUT_ADAPTER_DIR = BASE_DIR / "backend" / "llm" / "models" / "recoverai-lora"


def format_chat_prompt(example, tokenizer):
    messages = [
        {"role": "system", "content": example["system"]},
        {"role": "user", "content": example["user"]},
        {"role": "assistant", "content": example["assistant"]}
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(messages, tokenize=False)
    return f"{example['system']}\n\n{example['user']}\n\n{example['assistant']}"


def train_lora(
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
    jsonl_path: str = str(DATA_PATH),
    output_dir: str = str(OUTPUT_ADAPTER_DIR),
    max_steps: int = 20
) -> bool:
    """
    Executes LoRA parameter-efficient fine-tuning on Qwen2.5-0.5B-Instruct.
    Saves adapter files to output_dir (backend/llm/models/recoverai-lora).
    """
    jsonl_file = Path(jsonl_path)
    if not jsonl_file.exists():
        print(f"[RecoverAI LoRA Train] Training data not found at {jsonl_path}. Generating dataset...")
        from backend.llm.training_data import prepare_training_dataset
        prepare_training_dataset()

    print(f"[RecoverAI LoRA Train] Loading dataset from {jsonl_path}...")
    records = []
    with open(jsonl_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"[RecoverAI LoRA Train] Tokenizing {len(records)} examples for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True, cache_dir=os.getenv('HF_HOME'))
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    texts = [format_chat_prompt(rec, tokenizer) for rec in records]
    dataset = Dataset.from_dict({"text": texts})

    print(f"[RecoverAI LoRA Train] Loading base model {model_name}...")
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        trust_remote_code=True,
        cache_dir=os.getenv('HF_HOME')
    )

    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"]
    )

    model = get_peft_model(base_model, peft_config)
    model.print_trainable_parameters()

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        max_steps=max_steps,
        learning_rate=2e-4,
        logging_steps=5,
        save_strategy="no",
        use_cpu=True,
        report_to="none"
    )

    if TRL_AVAILABLE:
        print("[RecoverAI LoRA Train] Starting SFTTrainer execution...")
        trainer = SFTTrainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            dataset_text_field="text",
            max_seq_length=512,
        )
    else:
        print("[RecoverAI LoRA Train] TRL unavailable, using Standard Trainer...")
        from transformers import Trainer, DataCollatorForLanguageModeling
        
        def tokenize_function(examples):
            return tokenizer(examples["text"], truncation=True, max_length=512)

        tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=["text"])
        data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )

    trainer.train()

    print(f"[RecoverAI LoRA Train] Saving LoRA adapter to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("[RecoverAI LoRA Train] LoRA fine-tuning successfully completed!")
    return True


if __name__ == "__main__":
    train_lora()
