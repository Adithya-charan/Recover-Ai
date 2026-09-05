import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.schemas.transaction import TransactionInput
from backend.ml.features import extract_features
from backend.ml.model import RecoveryMLModel
from backend.ml.inference import predict_recovery_ml


class TestML(unittest.TestCase):

    def setUp(self):
        self.model = RecoveryMLModel()

    def test_feature_extraction(self):
        tx = TransactionInput(
            transaction_id="TX_ML_01",
            customer_id="C01",
            amount=2500,
            payment_status="failed",
            failure_reason="timeout",
            attempt_count=1
        )
        feats = extract_features(tx)
        self.assertEqual(feats["amount"], 2500.0)
        self.assertEqual(feats["attempt_count"], 1.0)
        self.assertIn("hist_success_ratio", feats)

    def test_ml_prediction_structure(self):
        tx = TransactionInput(
            transaction_id="TX_ML_02",
            customer_id="C02",
            amount=1999,
            payment_status="failed",
            failure_reason="timeout",
            attempt_count=1
        )
        res = predict_recovery_ml(tx)
        self.assertIn("recovery_probability", res)
        self.assertIn("risk_score", res)
        self.assertIn("risk_level", res)
        self.assertIn("expected_recovery_value", res)
        self.assertGreaterEqual(res["recovery_probability"], 0.0)
        self.assertLessEqual(res["recovery_probability"], 1.0)


if __name__ == "__main__":
    unittest.main()
