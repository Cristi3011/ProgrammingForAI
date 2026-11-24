"""NumPy inference for the Week 5 learned feed scorer."""
from __future__ import annotations

from pathlib import Path

import numpy as np


class LearnedScorer:
    def __init__(self, model_path: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parents[2]
        candidates = (
            [Path(model_path)] if model_path is not None else [
                root / "models" / "like_model.npz",
                root.parent / "lab-07" / "like_model.npz",
            ]
        )
        for path in candidates:
            if path.is_file():
                self.model_path = path
                break
        else:
            raise FileNotFoundError(
                "Missing learned model. Copy like_model.npz to "
                "instakill-starter/models/like_model.npz."
            )
        self.model = np.load(self.model_path, allow_pickle=False)
        names = [str(name) for name in self.model["features"].tolist()]
        if names != [
            "freshness",
            "affinity",
            "popularity",
            "activity",
            "lifetime",
            "age",
        ]:
            raise ValueError(f"Unexpected learned-model features: {names}")
        self.half_life_days = float(self.model["half_life_days"])
        self.popularity_days = float(self.model["popularity_days"])
        self.activity_cap = float(self.model["activity_cap"])
        self.age_cap_days = float(self.model["age_cap_days"])

    def predict(self, features: np.ndarray) -> np.ndarray:
        values = np.asarray(features, dtype=np.float64)
        if values.ndim != 2 or values.shape[1] != 6:
            raise ValueError("learned features must have shape (n_candidates, 6)")
        standardized = (values - self.model["mu"]) / self.model["sd"]
        hidden = np.tanh(
            standardized @ self.model["W1"] + self.model["b1"]
        )
        logits = (
            hidden @ self.model["W2"] + self.model["b2"]
        )[:, 0]
        logits = np.clip(logits, -60.0, 60.0)
        return 1.0 / (1.0 + np.exp(-logits))
