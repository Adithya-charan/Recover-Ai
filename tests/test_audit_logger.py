import csv
import os
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.audit_logger import AuditLogger, AUDIT_COLUMNS


class TestAuditLogger(unittest.TestCase):

    def _make_logger(self) -> AuditLogger:
        return AuditLogger()

    def _record(self, logger: AuditLogger, **overrides) -> dict:
        defaults = dict(
            transaction_id="TX01",
            customer_id="C01",
            amount=1000.0,
            payment_status="failed",
            failure_reason="timeout",
            risk_score=40,
            risk_level="medium",
            agent_diagnosis="Temporary failure",
            agent_action="retry",
            agent_confidence=0.92,
            agent_reason="Customer history good",
            policy_decision="ALLOW",
            policy_reason="Passed checks",
            execution_status="SIMULATED",
            recovery_status="RECOVERED",
            recovered_amount=1000.0,
            execution_message="Retry succeeded",
        )
        defaults.update(overrides)
        return logger.record_event(**defaults)

    def test_record_audit_event_fields(self):
        logger = self._make_logger()
        event = self._record(logger, case_type="PAYMENT_FAILURE", communication_attempts=2)
        self.assertEqual(event["transaction_id"], "TX01")
        self.assertEqual(event["policy_decision"], "ALLOW")
        self.assertEqual(event["recovery_status"], "RECOVERED")
        self.assertEqual(event["case_type"], "PAYMENT_FAILURE")
        self.assertEqual(event["communication_attempts"], 2)
        self.assertIn("executed_at", event)

    def test_provider_reference_persisted(self):
        """provider_reference and provider must survive CSV round-trip."""
        import tempfile, csv as _csv
        from unittest.mock import patch

        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False, mode="w", newline=""
        ) as tf:
            tmp = Path(tf.name)

        try:
            with patch("backend.services.audit_logger.AUDIT_CSV", tmp):
                logger = AuditLogger()
                self._record(
                    logger,
                    transaction_id="TX_PROV",
                    provider="sandbox",
                    provider_reference="order_sb_abc123",
                )
            with open(tmp, newline="", encoding="utf-8") as fh:
                rows = list(_csv.DictReader(fh))
            self.assertEqual(rows[0]["provider"], "sandbox")
            self.assertEqual(rows[0]["provider_reference"], "order_sb_abc123")
        finally:
            tmp.unlink(missing_ok=True)

    def test_communication_channel_persisted(self):
        """communication_channel must survive CSV round-trip."""
        import tempfile, csv as _csv
        from unittest.mock import patch

        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False, mode="w", newline=""
        ) as tf:
            tmp = Path(tf.name)

        try:
            with patch("backend.services.audit_logger.AUDIT_CSV", tmp):
                logger = AuditLogger()
                self._record(
                    logger,
                    transaction_id="TX_CHAN",
                    communication_channel="whatsapp,email",
                    communication_attempts=2,
                )
            with open(tmp, newline="", encoding="utf-8") as fh:
                rows = list(_csv.DictReader(fh))
            self.assertEqual(rows[0]["communication_channel"], "whatsapp,email")
            self.assertEqual(rows[0]["communication_attempts"], "2")
        finally:
            tmp.unlink(missing_ok=True)

    def test_new_columns_in_audit_columns_constant(self):
        """AUDIT_COLUMNS must include provider_reference, provider, communication_channel."""
        self.assertIn("provider_reference", AUDIT_COLUMNS)
        self.assertIn("provider", AUDIT_COLUMNS)
        self.assertIn("communication_channel", AUDIT_COLUMNS)

    def test_backward_compat_missing_new_fields_writes_empty(self):
        """Rows without new fields must still write — missing keys become empty string."""
        import tempfile, csv as _csv
        from unittest.mock import patch

        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False, mode="w", newline=""
        ) as tf:
            tmp = Path(tf.name)

        try:
            with patch("backend.services.audit_logger.AUDIT_CSV", tmp):
                logger = AuditLogger()
                # Intentionally omit new fields — must not raise
                self._record(logger, transaction_id="TX_COMPAT")
            with open(tmp, newline="", encoding="utf-8") as fh:
                rows = list(_csv.DictReader(fh))
            # New fields default to empty string when not provided
            self.assertEqual(rows[0]["provider_reference"], "")
            self.assertEqual(rows[0]["provider"], "")
            self.assertEqual(rows[0]["communication_channel"], "")
        finally:
            tmp.unlink(missing_ok=True)

    def test_get_logs_returns_recorded_events(self):
        logger = self._make_logger()
        self._record(logger, transaction_id="TX_A")
        self._record(logger, transaction_id="TX_B")
        logs = logger.get_logs()
        self.assertEqual(len(logs), 2)
        ids = [e["transaction_id"] for e in logs]
        self.assertIn("TX_A", ids)
        self.assertIn("TX_B", ids)

    def test_get_logs_is_instance_isolated(self):
        """Two AuditLogger instances must not share in-memory state."""
        a = self._make_logger()
        b = self._make_logger()
        self._record(a, transaction_id="TX_ONLY_A")
        self.assertEqual(len(a.get_logs()), 1)
        self.assertEqual(len(b.get_logs()), 0)

    def test_csv_persistence(self, tmp_path=None):
        """record_event must write a row to the audit CSV."""
        import tempfile, csv as _csv
        from unittest.mock import patch

        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False, mode="w", newline=""
        ) as tf:
            tmp = Path(tf.name)

        try:
            with patch("backend.services.audit_logger.AUDIT_CSV", tmp):
                logger = AuditLogger()
                self._record(logger, transaction_id="TX_CSV", case_type="CHECKOUT_ABANDONMENT")

            self.assertTrue(tmp.exists())
            with open(tmp, newline="", encoding="utf-8") as fh:
                rows = list(_csv.DictReader(fh))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["transaction_id"], "TX_CSV")
            self.assertEqual(rows[0]["case_type"], "CHECKOUT_ABANDONMENT")
        finally:
            tmp.unlink(missing_ok=True)

    def test_csv_appends_not_overwrites(self):
        """Multiple record_event calls must append rows, not overwrite."""
        import tempfile, csv as _csv
        from unittest.mock import patch

        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False, mode="w", newline=""
        ) as tf:
            tmp = Path(tf.name)

        try:
            with patch("backend.services.audit_logger.AUDIT_CSV", tmp):
                logger = AuditLogger()
                for i in range(3):
                    self._record(logger, transaction_id=f"TX_{i}")

            with open(tmp, newline="", encoding="utf-8") as fh:
                rows = list(_csv.DictReader(fh))
            self.assertEqual(len(rows), 3)
        finally:
            tmp.unlink(missing_ok=True)

    def test_persistence_failure_does_not_raise(self):
        """If the CSV path is unwriteable, record_event must not crash."""
        from unittest.mock import patch

        with patch("backend.services.audit_logger.AUDIT_CSV", Path("/invalid/path/audit.csv")):
            logger = AuditLogger()
            # Must not raise
            event = self._record(logger, transaction_id="TX_SAFE")
        self.assertEqual(event["transaction_id"], "TX_SAFE")


if __name__ == "__main__":
    unittest.main()
