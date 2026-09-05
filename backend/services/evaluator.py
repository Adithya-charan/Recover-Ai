import pandas as pd


def evaluate(input_file):

    dataframe = pd.read_csv(input_file)

    total_transactions = len(dataframe)

    failed_or_abandoned = dataframe[
        dataframe["payment_status"].isin([
            "failed",
            "abandoned"
        ])
    ]

    recovery_eligible = dataframe[
        dataframe["recovery_eligible"] == True
    ]

    recovery_attempts = dataframe[
        dataframe["execution_status"] == "EXECUTED"
    ]

    successful_recoveries = dataframe[
        dataframe["recovery_status"] == "RECOVERED"
    ]

    blocked_actions = dataframe[
        dataframe["execution_status"] == "BLOCKED"
    ]

    total_revenue_at_risk = recovery_eligible[
        "amount"
    ].sum()

    total_attempted_value = recovery_attempts[
        "amount"
    ].sum()

    total_recovered = successful_recoveries[
        "recovered_amount"
    ].sum()

    eligible_count = len(recovery_eligible)

    recovered_count = len(successful_recoveries)

    if eligible_count > 0:
        recovery_rate = (
            recovered_count / eligible_count
        ) * 100
    else:
        recovery_rate = 0

    if len(recovery_attempts) > 0:
        attempt_success_rate = (
            recovered_count / len(recovery_attempts)
        ) * 100
    else:
        attempt_success_rate = 0

    if total_revenue_at_risk > 0:
        revenue_recovery_rate = (
            total_recovered /
            total_revenue_at_risk
        ) * 100
    else:
        revenue_recovery_rate = 0

    print("=" * 60)
    print("RECOVERAI EVALUATION REPORT")
    print("=" * 60)

    print()

    print(
        f"Total transactions: "
        f"{total_transactions}"
    )

    print(
        f"Failed / abandoned transactions: "
        f"{len(failed_or_abandoned)}"
    )

    print(
        f"Recovery eligible transactions: "
        f"{eligible_count}"
    )

    print(
        f"Revenue at risk: "
        f"₹{total_revenue_at_risk:,.2f}"
    )

    print()

    print(
        f"Recovery attempts: "
        f"{len(recovery_attempts)}"
    )

    print(
        f"Attempted transaction value: "
        f"₹{total_attempted_value:,.2f}"
    )

    print()

    print(
        f"Successful recoveries: "
        f"{recovered_count}"
    )

    print(
        f"Simulated revenue recovered: "
        f"₹{total_recovered:,.2f}"
    )

    print()

    print(
        f"Recovery rate: "
        f"{recovery_rate:.2f}%"
    )

    print(
        f"Attempt success rate: "
        f"{attempt_success_rate:.2f}%"
    )

    print(
        f"Revenue recovery rate: "
        f"{revenue_recovery_rate:.2f}%"
    )

    print()

    print(
        f"Policy-blocked actions: "
        f"{len(blocked_actions)}"
    )

    print()

    print("=" * 60)


if __name__ == "__main__":

    evaluate(
        "data/execution_results.csv"
    )