from typing import Union, Dict, Any
from backend.schemas.transaction import TransactionInput
from backend.ml.model import RecoveryMLModel

_global_model = RecoveryMLModel()


def predict_recovery_ml(transaction: Union[TransactionInput, Dict[str, Any]]) -> Dict[str, Any]:
    return _global_model.predict(transaction)
