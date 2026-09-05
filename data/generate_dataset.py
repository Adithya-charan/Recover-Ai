import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


random.seed(42)


OUTPUT_FILE = Path(__file__).parent / "transactions.csv"

FAILURE_REASONS = [
    "timeout",
    "network_error",
    "bank_declined",
    "insufficient_funds",
    "authentication_failed",
    "upi_failure",
    "checkout_abandoned",
]

PAYMENT_STATUSES = [
    "success",
    "failed",
    "abandoned",
]


def generate_transaction(index):
    transaction_id = f"TX{index:05d}"
    customer_id = f"CUST{random.randint(1000, 1199)}"

    amount = random.choice([
        299,
        499,
        799,
        999,
        1299,
        1999,
        2499,
        3499,
        4999,
        7999,
        9999,
    ])

    status = random.choices(
        PAYMENT_STATUSES,
        weights=[55, 30, 15],
        k=1
    )[0]

    if status == "success":
        failure_reason = None
        attempt_count = random.randint(1, 2)

    elif status == "failed":
        failure_reason = random.choice(
            FAILURE_REASONS[:-1]
        )
        attempt_count = random.randint(1, 5)

    else:
        failure_reason = "checkout_abandoned"
        attempt_count = 0

    customer_previous_payments = random.randint(0, 15)

    customer_previous_failures = random.randint(
        0,
        min(5, customer_previous_payments + 1)
    )

    days_since_event = random.randint(0, 30)

    subscription_status = random.choice([
        "active",
        "inactive",
        "not_applicable",
    ])

    if status == "success":
        recovery_eligible = False

    elif failure_reason in [
        "timeout",
        "network_error",
        "upi_failure",
    ]:
        recovery_eligible = True

    elif status == "abandoned":
        recovery_eligible = True

    elif (
        failure_reason == "bank_declined"
        and attempt_count <= 2
    ):
        recovery_eligible = True

    else:
        recovery_eligible = False

    if recovery_eligible:
        if failure_reason in [
            "timeout",
            "network_error",
            "upi_failure",
        ]:
            recommended_action = "retry"

        elif failure_reason == "checkout_abandoned":
            recommended_action = "reminder"

        else:
            recommended_action = "retry"

    else:
        if status == "failed":
            recommended_action = "escalate"
        else:
            recommended_action = "stop"

    transaction_date = (
        datetime.now() -
        timedelta(days=days_since_event)
    )

    return {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "amount": amount,
        "payment_status": status,
        "failure_reason": failure_reason,
        "attempt_count": attempt_count,
        "customer_previous_payments": customer_previous_payments,
        "customer_previous_failures": customer_previous_failures,
        "days_since_event": days_since_event,
        "subscription_status": subscription_status,
        "recovery_eligible": recovery_eligible,
        "recommended_action": recommended_action,
        "transaction_date": transaction_date.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }


def main():
    transactions = []

    for index in range(1, 501):
        transactions.append(
            generate_transaction(index)
        )

    dataframe = pd.DataFrame(transactions)

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("=" * 60)
    print("RECOVERAI DATASET GENERATED")
    print("=" * 60)
    print(f"Records: {len(dataframe)}")
    print(f"File: {OUTPUT_FILE}")
    print()

    print("Payment status:")
    print(
        dataframe["payment_status"]
        .value_counts()
    )

    print()

    print("Recovery eligibility:")
    print(
        dataframe["recovery_eligible"]
        .value_counts()
    )

    print()

    print(
        f"Total transaction value: "
        f"₹{dataframe['amount'].sum():,.2f}"
    )

    recovery_value = dataframe.loc[
        dataframe["recovery_eligible"],
        "amount"
    ].sum()

    print(
        f"Potential revenue at risk: "
        f"₹{recovery_value:,.2f}"
    )


if __name__ == "__main__":
    main()