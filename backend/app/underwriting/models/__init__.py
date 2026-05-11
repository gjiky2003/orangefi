"""
OrangeFi Underwriting ML Models.

This package contains model weight configurations for the risk scorer.
The weights are used in a weighted scoring approach that approximates
an XGBoost-style gradient boosted model.

Model Version: v1.0.0
Training Data: OrangeFi historical loan performance (2024-2026)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_model_weights(
    version: Optional[str] = None,
) -> Dict[str, Any]:
    """Load model weights from the JSON configuration file.

    Parameters
    ----------
    version : str, optional
        Model version identifier. If None, loads the default.

    Returns
    -------
    dict
        Model weights and parameters.
    """
    weights_path = os.path.join(BASE_DIR, "model_weights.json")

    if not os.path.exists(weights_path):
        raise FileNotFoundError(
            f"Model weights not found at {weights_path}"
        )

    with open(weights_path, "r") as f:
        data = json.load(f)

    return data


def get_model_versions() -> list[Dict[str, Any]]:
    """Return list of available model versions.

    Returns
    -------
    list of dict
        Each entry: version, description, created_at.
    """
    try:
        data = load_model_weights()
        return [
            {
                "version": data.get("version", "v1.0.0"),
                "description": data.get("description", "Default model"),
                "feature_count": len(data.get("weights", {})),
                "created_at": data.get("created_at", "2026-01-01"),
            }
        ]
    except FileNotFoundError:
        return []
