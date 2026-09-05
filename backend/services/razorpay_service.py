import os
from pathlib import Path

import razorpay
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class RazorpayService:

    def __init__(self):
        # Load .env lazily inside __init__ so module import does not mutate
        # os.environ — which would contaminate test process state.
        load_dotenv(ENV_FILE, override=False)

        key_id = os.getenv("RAZORPAY_KEY_ID")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        if not key_id or not key_secret:
            raise ValueError(
                "Razorpay credentials are missing from .env"
            )

        self.client = razorpay.Client(
            auth=(key_id, key_secret)
        )

    def get_orders(self, count=10):
        return self.client.order.all({
            "count": count
        })