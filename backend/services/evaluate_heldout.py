import pandas as pd


def evaluate_heldout():

    dataframe = pd.read_csv(
        "data/transactions.csv"
    )

    # Keep the final 100 records completely held out.
    test_set = dataframe.tail(100).copy()

    # Ground truth:
    # recovery_eligible represents whether the
    # synthetic transaction is actually recoverable.
    actual = test_set[
        "recovery_eligible"
    ].astype(bool)

    # Simulate the RecoverAI decision using the
    # existing agent decision output.
    decisions = pd.read_csv(
        "data/recovery_decisions.csv"
    )

    predictions = decisions[
        decisions["transaction_id"].isin(
            test_set["transaction_id"]
        )
    ].copy()

    predicted = predictions[
        "agent_action"
    ].isin([
        "retry",
        "reminder"
    ])

    actual_values = actual.to_numpy()
    predicted_values = predicted.to_numpy()

    true_positive = (
        (predicted_values == True) &
        (actual_values == True)
    ).sum()

    false_positive = (
        (predicted_values == True) &
        (actual_values == False)
    ).sum()

    false_negative = (
        (predicted_values == False) &
        (actual_values == True)
    ).sum()

    true_negative = (
        (predicted_values == False) &
        (actual_values == False)
    ).sum()

    precision = (
        true_positive /
        (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0
    )

    recall = (
        true_positive /
        (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else 0
    )

    false_positive_rate = (
        false_positive /
        (false_positive + true_negative)
        if (false_positive + true_negative) > 0
        else 0
    )

    print("=" * 60)
    print("RECOVERAI HELD-OUT EVALUATION")
    print("=" * 60)

    print()

    print(
        f"Held-out transactions: "
        f"{len(test_set)}"
    )

    print()

    print("Confusion matrix:")

    print(
        f"True positives:  "
        f"{true_positive}"
    )

    print(
        f"False positives: "
        f"{false_positive}"
    )

    print(
        f"False negatives: "
        f"{false_negative}"
    )

    print(
        f"True negatives:  "
        f"{true_negative}"
    )

    print()

    print(
        f"Precision: "
        f"{precision * 100:.2f}%"
    )

    print(
        f"Recall: "
        f"{recall * 100:.2f}%"
    )

    print(
        f"False-positive rate: "
        f"{false_positive_rate * 100:.2f}%"
    )

    print()

    print("=" * 60)


if __name__ == "__main__":
    evaluate_heldout()