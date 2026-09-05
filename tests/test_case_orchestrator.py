import pytest
from backend.schemas.case import RecoveryCaseInput
from backend.services.case_orchestrator import process_orchestrated_case
from backend.services.case_manager import get_case_manager

@pytest.fixture
def base_case():
    return RecoveryCaseInput(
        case_id="TEST_001",
        case_type="PAYMENT_FAILURE",
        customer_id="cust_123",
        amount=100.0,
        currency="USD",
        metadata={"payment_method": "card"}
    )

def test_payment_failure_case(base_case):
    base_case.case_type = "PAYMENT_FAILURE"
    result = process_orchestrated_case(base_case)
    assert "case_result" in result

def test_checkout_abandonment_case(base_case):
    base_case.case_type = "CHECKOUT_ABANDONMENT"
    result = process_orchestrated_case(base_case)
    assert "case_result" in result

def test_failed_subscription_case(base_case):
    base_case.case_type = "FAILED_SUBSCRIPTION"
    result = process_orchestrated_case(base_case)
    assert "case_result" in result

def test_b2b_receivable_case(base_case):
    base_case.case_type = "B2B_RECEIVABLE"
    result = process_orchestrated_case(base_case)
    assert "case_result" in result

def test_mandate_failure_case(base_case):
    base_case.case_type = "MANDATE_FAILURE"
    result = process_orchestrated_case(base_case)
    assert "case_result" in result

def test_promise_to_pay_case(base_case):
    base_case.case_type = "PROMISE_TO_PAY"
    result = process_orchestrated_case(base_case)
    assert "case_result" in result

def test_case_manager():
    manager = get_case_manager()
    metrics = manager.calculate_batch_metrics()
    assert "overall_recovery_rate" in metrics
