import os
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

try:
    from peft import PeftModel
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False


class LocalLLM:
    """
    Real local Hugging Face instruction LLM inference engine.
    Supports base model loading (default: Qwen/Qwen2.5-0.5B-Instruct) and PEFT/LoRA adapter loading.
    Runs on CPU with deterministic generation and strict JSON output validation.
    """

    def __init__(self, model_name: Optional[str] = None, adapter_path: Optional[str] = None):
        self.model_name = model_name or os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
        self.adapter_path = adapter_path or os.environ.get("LLM_ADAPTER_PATH", "backend/llm/models/recoverai-lora")
        self.is_fine_tuned = False

        print(f"[RecoverAI LLM] Loading base model: {self.model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            cache_dir=os.getenv('HF_HOME')
        )


        base_model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,
            trust_remote_code=True,
            cache_dir=os.getenv('HF_HOME')
        )

        # Check if LoRA adapter directory exists and has config
        adapter_dir = Path(self.adapter_path)
        if PEFT_AVAILABLE and adapter_dir.exists() and (adapter_dir / "adapter_config.json").exists():
            print(f"[RecoverAI LLM] Found LoRA adapter at {self.adapter_path}. Loading fine-tuned adapter...")
            try:
                self.model = PeftModel.from_pretrained(base_model, str(adapter_dir))
                self.is_fine_tuned = True
                print("[RecoverAI LLM] Successfully loaded fine-tuned LoRA adapter!")
            except Exception as err:
                print(f"[RecoverAI LLM] Failed to load adapter: {err}. Falling back to base model.")
                self.model = base_model
        else:
            self.model = base_model

        self.model.eval()

    def generate(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if hasattr(self.tokenizer, "apply_chat_template"):
            prompt_text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            prompt_text = f"{system_prompt}\n\n{user_prompt}"

        inputs = self.tokenizer(prompt_text, return_tensors="pt")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False
            )

        generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        return self._parse_response(text)

    def _parse_response(self, text: str) -> Dict[str, Any]:
        # Remove markdown code fences if present (e.g. ```json ... ```)
        cleaned_text = re.sub(r"```(?:json)?", "", text).strip("` \n\r\t")

        match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
        if not match:
            return {
                "action": "stop",
                "diagnosis": "LLM response format invalid",
                "reason": f"Model returned unparseable text: {text[:100]}",
                "confidence": 0.50
            }

        try:
            data = json.loads(match.group(0))
        except Exception:
            return {
                "action": "stop",
                "diagnosis": "LLM JSON parse error",
                "reason": "Failed to parse JSON response from LLM.",
                "confidence": 0.50
            }

        action = str(data.get("action", "stop")).strip().lower()
        valid_actions = {"retry", "reminder", "escalate", "stop"}
        if action not in valid_actions:
            action = "stop"

        try:
            confidence = float(data.get("confidence", 0.80))
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.50

        diagnosis = str(data.get("diagnosis", "AI decision generated.")).strip()
        reason = str(data.get("reason", "Recommendation produced by local LLM inference.")).strip()

        if self.is_fine_tuned:
            diagnosis = f"[LoRA Fine-Tuned LLM] {diagnosis}"
        else:
            diagnosis = f"[Local LLM] {diagnosis}"

        return {
            "action": action,
            "diagnosis": diagnosis,
            "reason": reason,
            "confidence": confidence
        }


# Singleton Cached Instance
_global_local_llm: Optional[LocalLLM] = None


def get_local_llm() -> LocalLLM:
    global _global_local_llm
    if _global_local_llm is None:
        _global_local_llm = LocalLLM()
    return _global_local_llm