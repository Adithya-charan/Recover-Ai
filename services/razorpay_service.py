import os
from pathlib import Path

# pyrefly: ignore [missing-import]
import razorpay
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


class RazorpayService:

    def __init__(self):
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