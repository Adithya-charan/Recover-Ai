"""
Tests proving that recovery metrics and dashboard metrics use distinct, clearly
labelled data sources:

- /api/dashboard  →  data_source="historical_pipeline_csv"  (transactions.csv + execution_results.csv)
- /api/metrics    →  data_source="historical_pipeline_csv"  (same)
- /api/recovery/metrics  →  data_source="recovery_cases_live"  (recovery_cases.json via CaseManager)
- /api/recovery/batch-metrics  →  sourced from CaseManager (same as above)

Tests also verify that the authoritative live recovery metrics come from CaseManager.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.case_manager import RecoveryCaseManager

client = TestClient(app)


# ---------------------------------------------------------------------------
# Data-source label tests
# ---------------------------------------------------------------------------

class TestDashboardDataSource:
    def test_dashboard_labels_historical_source(self):
        res = client.get("/api/dashboard")
        assert res.status_code == 200
        data = res.json()
        assert data["data_source"] == "historical_pipeline_csv", (
            "/api/dashboard must declare data_source=historical_pipeline_csv"
        )

    def test_recovery_metrics_labels_live_source(self):
        res = client.get("/api/recovery/metrics")
        assert res.status_code == 200
        data = res.json()
        assert data["data_source"] == "recovery_cases_live", (
            "/api/recovery/metrics must declare data_source=recovery_cases_live"
        )


# ---------------------------------------------------------------------------
# Recovery metrics come from CaseManager
# ---------------------------------------------------------------------------

class TestRecoveryMetricsSource:
    def test_recovery_metrics_fields_present(self):
        res = client.get("/api/recovery/metrics")
        assert res.status_code == 200
        data = res.json()
        for field in [
            "total_cases", "total_revenue_at_risk", "total_eligible_cases",
            "total_recovery_attempts", "total_successful_recoveries",
            "total_recovered_amount", "overall_recovery_rate",
            "total_blocked_actions", "total_escalated_cases",
            "case_type_breakdown",
        ]:
            assert field in data, f"/api/recovery/metrics missing field: {field}"

    def test_recovery_metrics_matches_case_manager(self):
        """Values from /api/recovery/metrics must equal CaseManager.calculate_batch_metrics()."""
        from backend.services.case_manager import get_case_manager
        mgr = get_case_manager()
        expected = mgr.calculate_batch_metrics()

        res = client.get("/api/recovery/metrics")
        assert res.status_code == 200
        data = res.json()

        assert data["total_cases"] == expected["total_cases"]
        assert data["total_recovered_amount"] == expected["total_recovered_amount"]
        assert data["overall_recovery_rate"] == expected["overall_recovery_rate"]

    def test_batch_metrics_same_as_recovery_metrics(self):
        """Both /api/recovery/batch-metrics and /api/recovery/metrics read from CaseManager."""
        r1 = client.get("/api/recovery/batch-metrics").json()
        r2 = client.get("/api/recovery/metrics").json()
        assert r1["total_cases"] == r2["total_cases"]
        assert r1["total_recovered_amount"] == r2["total_recovered_amount"]
        assert r1["overall_recovery_rate"] == r2["overall_recovery_rate"]


# ---------------------------------------------------------------------------
# Dashboard and recovery metrics can differ (they represent different datasets)
# ---------------------------------------------------------------------------

class TestMetricsSeparation:
    def test_dashboard_has_total_transactions_key(self):
        """Dashboard counts all historical transactions — recovery metrics count cases."""
        res = client.get("/api/dashboard")
        assert res.status_code == 200
        assert "total_transactions" in res.json()

    def test_recovery_metrics_has_case_type_breakdown(self):
        """Recovery metrics have per-flow breakdown; dashboard does not."""
        res = client.get("/api/recovery/metrics")
        assert res.status_code == 200
        assert "case_type_breakdown" in res.json()

        dash = client.get("/api/dashboard").json()
        assert "case_type_breakdown" not in dash
