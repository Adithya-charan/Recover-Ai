import os
os.environ['HF_HOME'] = r'F:/Razorpay/.hf_cache'
from backend.llm.inference import get_local_llm

def test_inference():
    llm = get_local_llm()
    system_prompt = "You are a helpful AI for payment recovery decisions. Respond with a JSON object containing action, diagnosis, reason, confidence."
    user_prompt = "Transaction TX123 failed due to timeout, amount 1999, attempt 1. Is recovery eligible? What action do you recommend?"
    out = llm.generate(system_prompt, user_prompt)
    print('LLM output:', out)

if __name__ == '__main__':
    test_inference()
