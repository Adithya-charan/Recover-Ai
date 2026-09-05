import os
os.environ['HF_HOME'] = r'F:/Razorpay/.hf_cache'
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = 'Qwen/Qwen2.5-0.5B-Instruct'
print('Downloading tokenizer...')
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True, cache_dir=os.getenv('HF_HOME'))
print('Tokenizer loaded, vocab size:', len(tokenizer))
print('Downloading model...')
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype='float32', trust_remote_code=True, cache_dir=os.getenv('HF_HOME'))
print('Model loaded successfully')
